import uuid

import colink as CL
from colink import CoLink
from aiflows.messages import Message, FlowMessage
from aiflows.utils.io_utils import coflows_deserialize, coflows_serialize
from aiflows.utils.constants import (
    PUSH_ARGS_TRANSFER_PATH,
    COFLOWS_PATH,
)
from typing import Callable


class FlowFuture:
    def __init__(self, cl, msg_id):
        self.cl = cl
        self.colink_storage_key = f"{PUSH_ARGS_TRANSFER_PATH}:{msg_id}:response"
        self.output_interface = lambda data_dict,**kwargs: data_dict
        
        
    def try_get_message(self):
        """
        Non-blocking read, returns None if there is no response yet.
        """
        return FlowMessage.deserialize(self.cl.read_entry(self.colink_storage_key))

    def try_get_data(self):
        message = FlowMessage.deserialize(self.cl.read_entry(self.colink_storage_key))
        return message.data

    def get_message(self):
        """
        Blocking read, creates colink queue in background and subscribes to it.
        Probably shouldn't create queue and should have timeout.
        """

        message = FlowMessage.deserialize(self.cl.read_or_wait(self.colink_storage_key))
        message.data = self.output_interface(message.data)
        return message

    def get_data(self):
        message = FlowMessage.deserialize(self.cl.read_or_wait(self.colink_storage_key))
        return self.output_interface(message.data)
    
    def set_output_interface(self, ouput_interface: Callable):
        self.output_interface = ouput_interface


def push_to_flow(cl, target_user_id, target_flow_ref, message: Message):
    if target_user_id == "local" or target_user_id == cl.get_user_id():
        participants = [
            CL.Participant(
                user_id=cl.get_user_id(),
                role="receiver",
            ),
        ]
    else:
        participants = [
            CL.Participant(
                user_id=cl.get_user_id(),
                role="initiator",
            ),
            CL.Participant(
                user_id=target_user_id,
                role="receiver",
            ),
        ]

    push_msg_id = uuid.uuid4()
    cl.create_entry(
        f"{PUSH_ARGS_TRANSFER_PATH}:{push_msg_id}:msg",
        message.serialize(),
    )

    push_param = {
        "flow_id": target_flow_ref,
        "message_id": str(push_msg_id),
    }
    cl.run_task("coflows_push", coflows_serialize(push_param), participants, True)
    return push_msg_id


def show_dispatch(cl):
    ...


def mounted_flows_info(cl: CoLink, flow_type: str):
    ...
    # mount_entries_keys = cl.read_keys(
    #     prefix=f"{cl.get_user_id()}::{COFLOWS_PATH}:{flow_type}:mounts",
    #     include_history=False,
    # )

    # for key_path in mount_entries_keys:
    #     key_name = str(key_path).split("::")[1].split("@")[0]


def served_flows_info(cl: CoLink):
    serve_entries_keys = cl.read_keys(
        prefix=f"{cl.get_user_id()}::{COFLOWS_PATH}", include_history=False
    )

    served_flows_info = {}
    for key_path in serve_entries_keys:
        served_flow_info = {}

        key_name = str(key_path).split("::")[1].split("@")[0]
        flow_type = key_name.split(":")[1]

        default_dispatch_point = coflows_deserialize(
            cl.read_entry(f"{key_name}:default_dispatch_point")
        )
        served_flow_info["default_dispatch_point"] = default_dispatch_point

        mounted_flows_info(cl, flow_type)

        served_flows_info[flow_type] = served_flow_info

    return served_flows_info
