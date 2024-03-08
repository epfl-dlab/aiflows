import uuid

import colink as CL
from colink import CoLink, InstantServer, InstantRegistry
from aiflows.messages import Message, FlowMessage
from aiflows.utils.io_utils import coflows_deserialize, coflows_serialize
from aiflows.utils.constants import (
    PUSH_ARGS_TRANSFER_PATH,
    COFLOWS_PATH,
    INSTANCE_METADATA_PATH,
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


def start_colink_server() -> CoLink:
    InstantRegistry()
    cl = InstantServer().get_colink().switch_to_generated_user()
    cl.start_protocol_operator("coflows_scheduler", cl.get_user_id(), False)
    return cl
