import os
import sys
import argparse
from typing import List, Dict, Any
import hydra

import colink as CL
from colink import CoLink
from colink import ProtocolOperator
from aiflows.messages import FlowMessage
from aiflows.utils.general_helpers import (
    recursive_dictionary_update,
)
from aiflows.utils.coflows_utils import push_to_flow, PUSH_ARGS_TRANSFER_PATH
from aiflows.utils.serve_utils import (
    start_colink_component,
    get_instance_metadata
)
from aiflows.utils.io_utils import coflows_deserialize, coflows_serialize
from aiflows.utils.constants import DEFAULT_DISPATCH_POINT, FLOW_MODULES_BASE_PATH, COFLOWS_PATH


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
    curr_dir = os.getcwd()
    os.chdir(sys.path[-1])
    if config_overrides is not None:
        config = recursive_dictionary_update(config, config_overrides)
    flow = hydra.utils.instantiate(config, _recursive_=False, _convert_="partial")
    if state is not None:
        flow.__setflowstate__({"flow_state": state}, safe_mode=True)
    os.chdir(curr_dir)
    return flow


def dispatch_response(cl, output_message, reply_data):
    if "mode" not in reply_data:
        print("WARNING: dispatch response mode unknown.")
        return

    reply_mode = reply_data["mode"]

    if reply_mode == "no_reply":
        print("no_reply mode")
        return

    if reply_mode == "push":
        push_to_flow(
            cl=cl,
            target_user_id=reply_data["user_id"],
            target_flow_ref=reply_data["flow_ref"],
            message=output_message,
        )
    elif reply_mode == "storage":
        user_id = reply_data["user_id"]
        input_msg_id = reply_data["input_msg_id"]
        colink_storage_key = f"{PUSH_ARGS_TRANSFER_PATH}:{input_msg_id}:response"
        if user_id == cl.get_user_id():
            # local
            cl.create_entry(colink_storage_key, output_message.serialize())
        else:
            cl.remote_storage_create(
                [user_id],
                colink_storage_key,
                output_message.serialize(),
                False,
            )
    else:
        print("WARNING: dispatch response mode unknown.")


def dispatch_task_handler(cl: CoLink, param: bytes, participants: List[CL.Participant]):
    dispatch_task = coflows_deserialize(param)
    print("\n~~~ Dispatch task ~~~")
    flow_id = dispatch_task["flow_id"]

    # metadata can be in engine queues datastructure
    # metadata can be given in public param by scheduler
    instance_metadata = get_instance_metadata(cl, flow_id)

    if instance_metadata is None:
        print(f"Unknown flow instance {flow_id}.")

        # send empty responses
        for message_id in dispatch_task["message_ids"]:
            input_msg = FlowMessage.deserialize(
                cl.read_entry(f"{PUSH_ARGS_TRANSFER_PATH}:{message_id}:msg")
            )
            output_msg = FlowMessage(
                data={},
                src_flow=f"{cl.get_user_id()}:dispatch_worker",
                dst_flow=input_msg.src_flow,
                is_input_msg=False,
            )
            input_msg.reply_data["input_msg_id"] = message_id
            dispatch_response(cl, output_msg, input_msg.reply_data)
        return

    flow_type = instance_metadata["flow_type"]
    message_ids = dispatch_task["message_ids"]

    print(f"flow_type: {flow_type}")
    print(f"flow_id: {flow_id}")
    print(f"message_ids: {message_ids}\n")

    user_id = instance_metadata["user_id"]
    client_id = "local" if user_id == cl.get_user_id() else user_id
    serve_entry_path = f"{COFLOWS_PATH}:{flow_type}"
    mount_path = f"{serve_entry_path}:mounts:{client_id}:{flow_id}"

    default_config = coflows_deserialize(
        cl.read_entry(f"{serve_entry_path}:default_config")
    )
    config_overrides = coflows_deserialize(
        cl.read_entry(f"{mount_path}:config_overrides")
    )
    state = coflows_deserialize(cl.read_entry(f"{mount_path}:state"), use_pickle=True)

    flow = create_flow(default_config, config_overrides, state)
    flow.set_colink(cl)

    for message_id in dispatch_task["message_ids"]:
        input_msg = FlowMessage.deserialize(
            cl.read_entry(f"{PUSH_ARGS_TRANSFER_PATH}:{message_id}:msg")
        )

        input_msg.reply_data["input_msg_id"] = message_id

        output_msg = flow(input_msg)
        dispatch_response(cl, output_msg, input_msg.reply_data)

    new_state = flow.__getstate__()["flow_state"]
    cl.update_entry(
        f"{mount_path}:state", coflows_serialize(new_state, use_pickle=True)
    )


def run_dispatch_worker_thread(
    cl,
    dispatch_point=DEFAULT_DISPATCH_POINT,
    flow_modules_base_path=FLOW_MODULES_BASE_PATH,
):
    sys.path.append(flow_modules_base_path)
    pop = ProtocolOperator(__name__)

    proto_role = f"{dispatch_point}:local"
    pop.mapping[proto_role] = dispatch_task_handler

    pop.run_attach(cl=cl)
    print("Dispatch worker started in attached thread.")


# python dispatch-worker.py --addr http://127.0.0.1:2021 --jwt $(sed -n "1,1p" ./jwts.txt)
if __name__ == "__main__":
    args = parse_args()
    cl = start_colink_component("Dispatch worker", args)

    sys.path.append(args["flow_modules_base_path"])
    pop = ProtocolOperator(__name__)

    proto_role = args["dispatch_point"] + ":local"
    pop.mapping[proto_role] = dispatch_task_handler

    print("Dispatch worker started.")
    pop.run(
        cl=cl,
        keep_alive_when_disconnect=args["keep_alive"],
        vt_public_addr="127.0.0.1",  # HACK
        attached=False,
    )
