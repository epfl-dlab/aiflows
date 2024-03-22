import os
import sys
import argparse
from typing import List, Dict, Any
import hydra
import json
from threading import Thread

import colink as CL
from colink import CoLink
from colink import ProtocolOperator
from aiflows.messages import FlowMessage
from aiflows.utils.general_helpers import (
    recursive_dictionary_update,
    quick_load_api_keys,
)
from aiflows.utils.coflows_utils import (
    dispatch_response,
)
from aiflows.utils.serve_utils import (
    start_colink_component,
    _get_local_flow_instance_metadata,
)
from aiflows.utils.io_utils import coflows_deserialize, coflows_serialize
from aiflows.utils.constants import (
    DEFAULT_DISPATCH_POINT,
    FLOW_MODULES_BASE_PATH,
    COFLOWS_PATH,
)
from aiflows.backends.api_info import ApiInfo
from aiflows.utils import logging

log = logging.get_logger(__name__)

worker_api_infos = None


def parse_args():
    parser = argparse.ArgumentParser(description="Dispatch flow worker")

    env_addr = os.getenv("COLINK_CORE_ADDR")
    env_jwt = os.getenv("COLINK_JWT")

    parser.add_argument(
        "--addr",
        type=str,
        default=env_addr,
        required=env_addr is None,
        help="CoLink server address.",
    )
    parser.add_argument(
        "--jwt",
        type=str,
        default=env_jwt,
        required=env_jwt is None,
        help="Your JWT issued by the CoLink server.",
    )
    parser.add_argument(
        "--flow_modules_base_path",
        type=str,
        default=FLOW_MODULES_BASE_PATH,
        help="Path to directory that contains the flow_modules directory.",
    )
    parser.add_argument(
        "--dispatch_point",
        type=str,
        default=DEFAULT_DISPATCH_POINT,
        help="Dispatch point to which the workers will subscribe to.",
    )
    parser.add_argument(
        "--keep_alive",
        type=bool,
        default=False,
        help="Keep alive when disconnected from colink server.",
    )

    args = parser.parse_args()
    return vars(args)


def create_flow(
    config: Dict[str, Any],
    config_overrides: Dict[str, Any] = None,
    state: Dict[str, Any] = None,
):
    """Creates a flow from the given config and state.

    :param config: flow config
    :type config: Dict[str, Any]
    :param config_overrides: flow config overrides
    :type config_overrides: Dict[str, Any]
    :param state: flow state
    :type state: Dict[str, Any]
    """
    if config_overrides is not None:
        config = recursive_dictionary_update(config, config_overrides)

    if worker_api_infos is not None:
        quick_load_api_keys(config, worker_api_infos)

    flow = hydra.utils.instantiate(config, _recursive_=False, _convert_="partial")
    if state is not None:
        flow.__setflowstate__({"flow_state": state}, safe_mode=True)

    return flow


def dispatch_task_handler(cl: CoLink, param: bytes, participants: List[CL.Participant]):
    """Dispatches a task to and runs the appropriate flow on a message.

    :param cl: The colink object
    :type cl: CL.Colink
    :param param: The serialized dispatch task
    :type param: bytes
    :param participants: The participants involved in the task
    :type participants: List[colink.Participant]
    """
    dispatch_task = coflows_deserialize(param)
    log.info("\n~~~ Dispatch task ~~~")
    flow_id = dispatch_task["flow_id"]

    # metadata can be in engine queues datastructure
    # metadata can be given in public param by scheduler
    instance_metadata = _get_local_flow_instance_metadata(cl, flow_id)
    if instance_metadata is None:
        log.info(f"Unknown flow instance {flow_id}.")

        if flow_id == "storage":  # HACK remove this when push worker handles storage
            return

        # send empty responses
        for message_path in dispatch_task["message_ids"]:
            input_msg = FlowMessage.deserialize(cl.read_entry(message_path))
            output_msg = FlowMessage(
                data={"error": "Unknown flow instance!"},
                src_flow=f"{cl.get_user_id()}:dispatch_worker",
                dst_flow=input_msg.src_flow,
            )
            input_msg.reply_data["input_msg_path"] = message_path
            dispatch_response(cl, output_msg, input_msg.reply_data)
        return

    flow_endpoint = instance_metadata["flow_endpoint"]
    message_paths = dispatch_task["message_ids"]
    user_id = instance_metadata["user_id"]  # of user who mounted flow
    client_id = "local" if user_id == cl.get_user_id() else user_id

    # get serve data
    serve_entry_path = f"{COFLOWS_PATH}:{flow_endpoint}"
    parallel_dispatch = bool(
        int.from_bytes(
            cl.read_entry(f"{serve_entry_path}:parallel_dispatch"),
            byteorder="little",
            signed=True,
        )
    )
    # default_config = coflows_deserialize(
    #     cl.read_entry(f"{serve_entry_path}:default_config")
    # )

    log.info(f"flow_endpoint: {flow_endpoint}")
    log.info(f"flow_id: {flow_id}")
    log.info(f"owner_id: {user_id}")
    log.info(f"message_paths: {message_paths}")
    log.info(f"parallel_dispatch: {parallel_dispatch}\n")

    config_overrides = None
    state = None

    # get instance data
    mount_path = f"{serve_entry_path}:mounts:{client_id}:{flow_id}"
    config_overrides = coflows_deserialize(
        cl.read_entry(f"{mount_path}:config_overrides")
    )
    state = coflows_deserialize(cl.read_entry(f"{mount_path}:state"), use_pickle=True)

    if config_overrides is None:
        log.error("ERROR: no config to load flow.")
        return

    try:
        # TODO would be better to have pickled flow in colink storage
        flow = create_flow(None, config_overrides, state)
        flow.set_colink(cl)

        for message_path in dispatch_task["message_ids"]:
            input_msg = FlowMessage.deserialize(cl.read_entry(message_path))
            log.info(f"Input message source: {input_msg.src_flow}")

            input_msg.reply_data["input_msg_path"] = message_path
            flow(input_msg)

    except Exception as e:
        log.info(f"Error executing flow: {e}")
        return

    if not parallel_dispatch:
        new_state = flow.__getstate__()["flow_state"]
        cl.update_entry(
            f"{mount_path}:state", coflows_serialize(new_state, use_pickle=True)
        )


def run_dispatch_worker_thread(
    cl,
    dispatch_point=DEFAULT_DISPATCH_POINT,
    flow_modules_base_path=FLOW_MODULES_BASE_PATH,
    api_infos: List[ApiInfo] = None,
):
    """Runs a dispatch worker in a separate thread.

    :param cl: colink object
    :type cl: CoLink
    :param dispatch_point: dispatch point to which the workers will subscribe to
    :type dispatch_point: str
    :param flow_modules_base_path: path to directory that contains the flow_modules directory
    :type flow_modules_base_path: str
    """
    # sys.path.append(flow_modules_base_path)
    global worker_api_infos
    worker_api_infos = api_infos
    pop = ProtocolOperator(__name__)

    proto_role = f"{dispatch_point}:local"
    pop.mapping[proto_role] = dispatch_task_handler

    thread = Thread(target=pop.run, args=(cl, False, None, True), daemon=True)
    thread.start()
    log.info("Dispatch worker started in attached thread.")
    log.info(f"dispatch_point: {dispatch_point}")


def run_dispatch_worker_threads(
    cl,
    num_workers,
    dispatch_point=DEFAULT_DISPATCH_POINT,
    flow_modules_base_path=FLOW_MODULES_BASE_PATH,
):
    """Runs multiple dispatch workers in separate threads.

    :param cl: colink object
    :type cl: CoLink
    :param num_workers: number of workers to run
    :type num_workers: int
    :param dispatch_point: dispatch point to which the workers will subscribe to
    :type dispatch_point: str
    :param flow_modules_base_path: path to directory that contains the flow_modules directory
    :type flow_modules_base_path: str
    """
    for i in range(num_workers):
        run_dispatch_worker_thread(cl, dispatch_point, flow_modules_base_path)


# python dispatch-worker.py --addr http://127.0.0.1:2021 --jwt $(sed -n "1,1p" ./jwts.txt)
if __name__ == "__main__":
    args = parse_args()
    cl = start_colink_component("Dispatch worker", args)

    sys.path.append(args["flow_modules_base_path"])
    pop = ProtocolOperator(__name__)

    proto_role = args["dispatch_point"] + ":local"
    pop.mapping[proto_role] = dispatch_task_handler

    log.info("Dispatch worker started.")
    pop.run(
        cl=cl,
        keep_alive_when_disconnect=args["keep_alive"],
        attached=False,
    )
