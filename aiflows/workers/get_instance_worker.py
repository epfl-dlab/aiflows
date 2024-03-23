import os, sys
import json
import argparse
from threading import Thread
from typing import List

import colink as CL
from colink import CoLink, ProtocolOperator

from aiflows.utils import serve_utils
from aiflows.utils.constants import (
    GET_INSTANCE_CALLS_TRANSFER_PATH,
    FLOW_MODULES_BASE_PATH,
)
from aiflows.utils.io_utils import coflows_deserialize, coflows_serialize
from aiflows.utils import logging
log = logging.get_logger(__name__)

def parse_args():
    parser = argparse.ArgumentParser(description="get_instance worker")

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
        "--keep_alive",
        type=bool,
        default=False,
        help="Keep alive when disconnected from colink server.",
    )

    args = parser.parse_args()
    return vars(args)


def get_instances_initiator_handler(
    cl: CoLink, param: bytes, participants: List[CL.Participant]
):
    """ Initiator handler for get_instances (for fetching flow instances from participants via colink)
    
    :param cl: colink object
    :type cl: CoLink
    :param param: parameters
    :type param: bytes
    :param participants: list of participants involved in task
    :type participants: List[CL.Participant]
    """
    log.info("\n~~~ get_instances initiator ~~~")
    log.info(f"task_id = {cl.get_task_id()}")
    request_id = coflows_deserialize(param)
    get_instance_calls = coflows_deserialize(
        cl.read_entry(
            f"{GET_INSTANCE_CALLS_TRANSFER_PATH}:{request_id}:get_instance_calls"
        )
    )

    get_instances_results = {}
    for participant in participants[1:]:
        user_get_instance_calls = get_instance_calls[participant.user_id]
        # [(subflow_key, subflow_type, subflow_config_overrides)]
        cl.send_variable(
            "user_get_instance_calls",
            coflows_serialize(user_get_instance_calls),
            [participant],
        )

    for participant in participants[1:]:
        user_get_instances_results = coflows_deserialize(
            cl.recv_variable("get_instances_results", participant)
        )  # Dict: subflow_key -> flow_id
        get_instances_results.update(user_get_instances_results)

    log.info(f'Received subflow instances: {json.dumps(get_instances_results, indent=4)}')
    cl.create_entry(
        f"{GET_INSTANCE_CALLS_TRANSFER_PATH}:{request_id}:get_instances_results",
        coflows_serialize(get_instances_results),
    )


def get_instances_receiver_handler(
    cl: CoLink, param: bytes, participants: List[CL.Participant]
):
    """ Receiver handler for get_instances (for fetching flow instances from participants via colink)
    
    :param cl: colink object
    :type cl: CoLink
    :param param: parameters
    :type param: bytes
    :param participants: list of participants involved in task
    :type participants: List[CL.Participant]
    """
    log.info("\n~~~ serving get_instances request ~~~")
    log.info(f"task_id = {cl.get_task_id()}")
    get_instance_calls = coflows_deserialize(
        cl.recv_variable("user_get_instance_calls", participants[0])
    )
    log.info(f'get_instance_calls: {get_instance_calls}')

    get_instance_results = {}
    for flow_key, flow_endpoint, config_overrides in get_instance_calls:
        try:
            flow_id = serve_utils._get_local_flow_instance(
                cl=cl,
                client_id=participants[0].user_id,
                flow_endpoint=flow_endpoint,
                config_overrides=config_overrides,
                initial_state=None,
                dispatch_point_override=None,
            )
            get_instance_results[flow_key] = {
                "flow_id": flow_id,
                "successful": True,
                "message": "Fetched local flow instance.",
            }
        except serve_utils.FlowInstanceException as e:
            get_instance_results[flow_key] = {
                "flow_id": "",
                "successful": False,
                "message": e.message,
            }

    cl.send_variable(
        "get_instances_results",
        coflows_serialize(get_instance_results),
        [participants[0]],
    )


def run_get_instance_worker_thread(
    cl,
):
    """ Runs get_instance worker in a thread.
    
    :param cl: colink object
    :type cl: CoLink
    """
    pop = ProtocolOperator(__name__)

    pop.mapping["coflows_get_instances:initiator"] = get_instances_initiator_handler
    pop.mapping["coflows_get_instances:receiver"] = get_instances_receiver_handler

    thread = Thread(target=pop.run, args=(cl, False, None, True), daemon=True)
    thread.start()
    log.info(
        f'get_instances worker started in attached thread for user {cl.get_user_id()}',
    )


# python get_instance_worker.py --addr http://127.0.0.1:2021 --jwt $(sed -n "1,1p" ./jwts.txt)
if __name__ == "__main__":
    args = parse_args()
    cl = serve_utils.start_colink_component("get_instances worker", args)

    sys.path.append(args["flow_modules_base_path"])
    pop = ProtocolOperator(__name__)
    pop.mapping["coflows_get_instances:initiator"] = get_instances_initiator_handler
    pop.mapping["coflows_get_instances:receiver"] = get_instances_receiver_handler

    log.info("get_instances worker started.")
    pop.run(
        cl=cl,
        keep_alive_when_disconnect=args["keep_alive"],
        attached=False,
    )
