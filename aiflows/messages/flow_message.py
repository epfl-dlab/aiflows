from dataclasses import dataclass
from typing import List, Any, Dict, Optional,Union
import colorama
from aiflows.messages import Message
from aiflows.utils.io_utils import coflows_deserialize
colorama.init()


# ToDo: When logging the "\n" in the nested messages is not mapped to a new line which makes it hard to debug. Fix that.

@dataclass
class FlowMessage(Message):
    
    def __init__(
        self,
        data: Dict[str, Any],
        src_flow: str = "unknown",
        src_flow_id: str = "unknown",
        dst_flow: str = "unknown",
        reply_data: Optional[Dict[str, Any]] = {"mode": "no_reply"},
        created_by: Optional[str] = None,
        private_keys: Optional[List[str]] = None,
        input_message_id: Optional[str] = None,
        is_reply: Optional[bool] = False,
        user_id: Optional[str] = None,
    ):
        created_by = src_flow if created_by is None else created_by
        super().__init__(data=data, created_by=created_by, private_keys=private_keys)
        self.src_flow_id = src_flow_id
        self.reply_data = reply_data
        self.src_flow = src_flow
        self.dst_flow = dst_flow
        self.input_message_id = self.message_id if input_message_id is None else input_message_id
        self.is_reply = is_reply
        self.user_id = user_id
        
    def to_string(self):
        src_flow = self.src_flow
        dst_flow = self.dst_flow
        display_msg_name = "FlowMessage"
        message = (
            f"\n{colorama.Fore.GREEN} ~~~ {display_msg_name}: `{src_flow}` --> `{dst_flow}` ~~~\n"
            f"{colorama.Fore.WHITE}{self.__str__()}{colorama.Style.RESET_ALL}"
        )

        return message

@dataclass
class UpdateMessage_Generic(Message):
    r"""Updates the message of a flow.

    :param updated_flow: The name of the flow that should be updated
    :type updated_flow: str
    :param \**kwargs: arguments that are passed to the Message constructor
    """

    def __init__(self, updated_flow: str, **kwargs):
        super().__init__(**kwargs)
        self.updated_flow = updated_flow

    def to_string(self):
        """Returns a string representation of the message.

        :return: The string representation of the message.
        :rtype: str
        """
        updated_flow = self.updated_flow

        message = (
            f"\n{colorama.Fore.MAGENTA} ~~~ UpdateMessage ({self.__class__.__name__}): `{updated_flow}` ~~~\n"
            f"{colorama.Fore.WHITE}{self.__str__()}{colorama.Style.RESET_ALL}"
        )

        return message


@dataclass
class UpdateMessage_ChatMessage(UpdateMessage_Generic):
    r"""Updates the chat message of a flow.

    :param content: The content of the chat message
    :type content: str
    :param role: The role of the chat message (typically "user", "assistant", "system", "human" ...)
    :type role: str
    :param updated_flow: The name of the flow that should be updated
    :type updated_flow: str
    :param \**kwargs: arguments that are passed to the UpdateMessage_Generic constructor
    """

    def __init__(self, content: str, role: str, updated_flow: str, **kwargs):
        super().__init__(data={}, updated_flow=updated_flow, **kwargs)
        self.data["role"] = role
        self.data["content"] = content

    def to_string(self):
        """Returns a string representation of the message.

        :return: The string representation of the message.
        :rtype: str
        """
        updated_flow = self.updated_flow
        role = self.data["role"]
        color = colorama.Fore.RED if role == "assistant" else colorama.Fore.YELLOW

        message = (
            f"\n{color} ~~~ UpdateMessage ({self.__class__.__name__}): "
            f"`{updated_flow}` (role: {role}) ~~~\n"
            f"{colorama.Fore.WHITE}{self.__str__()}{colorama.Style.RESET_ALL}"
        )

        return message


@dataclass
class UpdateMessage_NamespaceReset(Message):
    """Resets the namespace of a flow's message."""

    def __init__(self, updated_flow: str, created_by: str, keys_deleted_from_namespace: List[str]):
        super().__init__(created_by=created_by, data={})
        self.updated_flow = updated_flow
        self.data["keys_deleted_from_namespace"] = keys_deleted_from_namespace

    def to_string(self):
        """Returns a string representation of the message.

        :return: The string representation of the message.
        :rtype: str
        """
        updated_flow = self.updated_flow

        message = (
            f"\n{colorama.Fore.CYAN} ~~~ ResetMessageNamespaceOnly ({self.__class__.__name__}): `{updated_flow}` ~~~\n"
            f"{colorama.Fore.WHITE}{self.__str__()}{colorama.Style.RESET_ALL}"
        )

        return message


@dataclass
class UpdateMessage_FullReset(Message):
    """Resets the full message of a flow.

    :param updated_flow: The name of the flow that should be updated

    """

    def __init__(self, updated_flow: str, created_by: str, keys_deleted_from_namespace: List[str]):
        super().__init__(created_by=created_by, data={})
        self.updated_flow = updated_flow
        self.data["keys_deleted_from_namespace"] = keys_deleted_from_namespace

    def to_string(self):
        """Returns a string representation of the message.

        :return: The string representation of the message.
        :rtype: str
        """
        updated_flow = self.updated_flow

        message = (
            f"\n{colorama.Fore.CYAN} ~~~ ResetMessageFull ({self.__class__.__name__}): `{updated_flow}` ~~~\n"
            f"{colorama.Fore.WHITE}{self.__str__()}{colorama.Style.RESET_ALL}"
        )

        return message
        
