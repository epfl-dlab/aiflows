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
from aiflows.utils import logging

log = logging.get_logger(__name__)


class FlowFuture:
    """A future object that represents a response from a flow. One can use this object to read the response from the flow."""

    def __init__(self, cl, message_path):
        self.cl = cl
        self.colink_storage_key = f"{message_path.rpartition(':')[0]}:response"
        self.output_interface = lambda data_dict, **kwargs: data_dict

    def __str__(self):
        return f"FlowFuture(user_id={self.cl.get_user_id()}, colink_storage_key='{self.colink_storage_key}')"

    def try_get_message(self):
        """
        Non-blocking read, returns None if there is no response yet.
        """
        return FlowMessage.deserialize(self.cl.read_entry(self.colink_storage_key))

    def try_get_data(self):
        message = FlowMessage.deserialize(self.cl.read_entry(self.colink_storage_key))
        return message.data

    def get_message(self):
        """Blocking read of the future returns a message."""
        message = FlowMessage.deserialize(self.cl.read_or_wait(self.colink_storage_key))
        message.data = self.output_interface(message.data)
        return message

    def get_data(self):
        """Blocking read of the future returns a dictionary of the data."""
        message = FlowMessage.deserialize(self.cl.read_or_wait(self.colink_storage_key))
        return self.output_interface(message.data)

    def set_output_interface(self, ouput_interface: Callable):
        """Set the output interface for the future."""
        self.output_interface = ouput_interface


def push_to_flow(
    cl: CL.colink, target_user_id: str, target_flow_id: str, message: FlowMessage
):
    """Pushes a message to a flow via colink

    :param cl: The colink object
    :type cl: CL.colink
    :param target_user_id: The user id of the flow we're pushing to
    :type target_user_id: str
    :param target_flow_id: The flow id of the flow we're pushing to
    :type target_flow_id: str
    :param message: The message to push
    :type message: FlowMessage
    """
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
    push_msg_path = f"{PUSH_ARGS_TRANSFER_PATH}:{push_msg_id}:msg"
    cl.create_entry(
        push_msg_path,
        message.serialize(),
    )

    push_param = {  # NOTE scheduler reads this
        "flow_id": target_flow_id,
        "message_id": push_msg_path,  # TODO return back to just id, need to change push worker
    }
    cl.run_task("coflows_push", coflows_serialize(push_param), participants, True)
    return push_msg_path


def dispatch_response(cl, output_message, reply_data):
    """Dispatches a response message to the appropriate flow.

    :param cl: The colink object
    :type cl: CL.Colink
    :param output_message: The output message
    :type output_message: FlowMessage
    :param reply_data: The meta data describing how to reply
    """

    if "mode" not in reply_data:
        log.warn("WARNING: dispatch response mode unknown.")
        return

    reply_mode = reply_data["mode"]

    if reply_mode == "no_reply":
        log.info("no_reply mode")
        return

    if reply_mode == "push":
        push_to_flow(
            cl=cl,
            target_user_id=reply_data["user_id"],
            target_flow_id=reply_data["flow_id"],
            message=output_message,
        )
    elif reply_mode == "storage":
        # TODO we can probably reuse push_to_flow for this
        user_id = reply_data["user_id"]
        message_path = reply_data["input_msg_path"]
        colink_storage_key = f"{message_path.rpartition(':')[0]}:response"

        if user_id == cl.get_user_id():
            # local
            cl.update_entry(colink_storage_key, output_message.serialize())
        else:
            participants = [
                CL.Participant(
                    user_id=cl.get_user_id(),
                    role="initiator",
                ),
                CL.Participant(
                    user_id=reply_data["user_id"],
                    role="receiver",
                ),
            ]
            cl.update_entry(
                colink_storage_key,
                output_message.serialize(),
            )
            push_param = {  # NOTE scheduler reads this
                "flow_id": "storage",
                "message_id": colink_storage_key,
            }
            cl.run_task(
                "coflows_push", coflows_serialize(push_param), participants, True
            )
    else:
        log.warn("WARNING: dispatch response mode unknown.")
