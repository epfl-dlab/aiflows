import os

import colink as CL
from colink import CoLink
from colink import decode_jwt_without_validation

from aiflows import flow_verse
from aiflows.backends.api_info import ApiInfo

import pickle
import json
import argparse


from termcolor import colored

from colink import CoLink, ProtocolOperator
import colink as CL

import time

from typing import List
from aiflows.utils import serve_utils
from aiflows.utils.constants import MOUNT_ARGS_TRANSFER_PATH
from aiflows.utils.io_utils import coflows_deserialize, coflows_serialize


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
        "--keep_alive",
        type=bool,
        default=False,
        help="Keep alive when disconnected from colink server.",
    )

    args = parser.parse_args()
    return vars(args)


def mount_initiator_handler(
    cl: CoLink, param: bytes, participants: List[CL.Participant]
):
    print("\n~~~ Mount Initiator Task ~~~")
    mount_id = coflows_deserialize(param)
    mount_args = coflows_deserialize(
        cl.read_entry(f"{MOUNT_ARGS_TRANSFER_PATH}:{mount_id}:mount_args")
    )

    flow_ids = {}
    for participant in participants[1:]:
        user_mount_tasks = mount_args[participant.user_id]
        # [(subflow_key, subflow_type, subflow_config_overrides)]
        cl.send_variable(
            "mount_tasks", coflows_serialize(user_mount_tasks), [participant]
        )

    for participant in participants[1:]:
        user_mount_completions = coflows_deserialize(
            cl.recv_variable("mount_completions", participant)
        )  # Dict: subflow_key -> flow_id
        flow_ids.update(user_mount_completions)

    print("Received subflow ids:", json.dumps(flow_ids, indent=4))
    cl.create_entry(
        f"{MOUNT_ARGS_TRANSFER_PATH}:{mount_id}:flow_ids",
        coflows_serialize(flow_ids),
    )


def mount_receiver_handler(
    cl: CoLink, param: bytes, participants: List[CL.Participant]
):
    print("\n~~~ Mount Receiver Task ~~~")
    my_mount_tasks = coflows_deserialize(
        cl.recv_variable("mount_tasks", participants[0])
    )

    flow_ids = {}
    for flow_key, flow_endpoint, config_overrides in my_mount_tasks:
        try:
            flow_id = serve_utils._get_local_flow_instance(
                cl=cl,
                client_id=participants[0].user_id,
                flow_endpoint=flow_endpoint,
                config_overrides=config_overrides,
                initial_state=None,
                dispatch_point_override=None,
            )
            flow_ids[flow_key] = flow_id
        except Exception:
            flow_ids[flow_key] = ""
            # TODO {"status": "ERROR", "flow_id": flow_id}

    cl.send_variable(
        "mount_completions", coflows_serialize(flow_ids), [participants[0]]
    )


def run_mount_worker_thread(
    cl,
):
    pop = ProtocolOperator(__name__)

    pop.mapping["coflows_mount:initiator"] = mount_initiator_handler
    pop.mapping["coflows_mount:receiver"] = mount_receiver_handler

    pop.run_attach(cl=cl)
    print("Mount worker started in attached thread for user ", cl.get_user_id())


# python mount-worker.py --addr http://127.0.0.1:2021 --jwt $(sed -n "1,1p" ./jwts.txt)
if __name__ == "__main__":
    args = parse_args()
    cl = serve_utils.start_colink_component("Mount worker", args)

    pop = ProtocolOperator(__name__)
    pop.mapping["coflows_mount:initiator"] = mount_initiator_handler
    pop.mapping["coflows_mount:receiver"] = mount_receiver_handler

    print("Mount worker started.")
    pop.run(
        cl=cl,
        keep_alive_when_disconnect=args["keep_alive"],
        vt_public_addr="127.0.0.1",  # HACK
        attached=False,
    )
