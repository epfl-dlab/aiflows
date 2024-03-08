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