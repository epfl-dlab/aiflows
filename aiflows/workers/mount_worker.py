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
from utils import (
    start_colink_component,
    coflows_deserialize,
    coflows_serialize,
    recursive_mount,
    MOUNT_ARGS_TRANSFER_PATH,
)


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


pop = ProtocolOperator(__name__)


@pop.handle("mount:initiator")
def mount_initiator_handler(
    cl: CoLink, param: bytes, participants: List[CL.Participant]
):
    mount_id = coflows_deserialize(param)
    mount_args = coflows_deserialize(
        cl.read_entry(f"{MOUNT_ARGS_TRANSFER_PATH}:{mount_id}:mount_args")
    )

    flow_refs = {}
    for participant in participants[1:]:
        user_mount_tasks = mount_args[participant.user_id]
        # [(subflow_key, subflow_type, subflow_config_overrides)]
        cl.send_variable(
            "mount_tasks", coflows_serialize(user_mount_tasks), [participant]
        )

    for participant in participants[1:]:
        user_mount_completions = coflows_deserialize(
            cl.recv_variables("mount_completions", participant)
        )  # Dict: subflow_key -> flow_ref
        flow_refs.update(user_mount_completions)

    cl.create_entry(
        f"{MOUNT_ARGS_TRANSFER_PATH}:{mount_id}:flow_refs",
        coflows_serialize(flow_refs),
    )


@pop.handle("mount:receiver")
def mount_receiver_handler(
    cl: CoLink, param: bytes, participants: List[CL.Participant]
):
    my_mount_tasks = coflows_deserialize(
        cl.recv_variables("mount_tasks", participants[0])
    )

    flow_refs = {}
    for flow_key, flow_type, config_overrides in my_mount_tasks:
        flow_ref = recursive_mount(
            cl=cl,
            client_id=participants[0].user_id,
            flow_type=flow_type,
            config_overrides=config_overrides,
            initial_state=None,  # ??
            dispatch_point_override=None,  # ??
        )
        flow_refs[flow_key] = flow_ref

    cl.send_variable(
        "mount_completions", coflows_serialize(flow_refs), [participants[0]]
    )


# python mount-worker.py --addr http://127.0.0.1:2021 --jwt $(sed -n "1,1p" ./jwts.txt)
if __name__ == "__main__":
    args = parse_args()
    cl = start_colink_component("Mount worker", args)

    vt_public_addr = "127.0.0.1"  # HACK
    pop.run(
        cl=cl,
        keep_alive_when_disconnect=args["keep_alive"],
        vt_public_addr=vt_public_addr,
        attached=False,
    )
