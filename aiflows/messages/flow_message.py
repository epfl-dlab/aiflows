from dataclasses import dataclass
from typing import List, Any, Dict, Optional
import colorama

from aiflows.messages import Message

colorama.init()


# ToDo: When logging the "\n" in the nested messages is not mapped to a new line which makes it hard to debug. Fix that.


@dataclass
class InputMessage(Message):
    """This class represents an input message that is passed from one flow to another.

    :param data_dict: The data content of the message
    :type data_dict: Dict[str, Any]
    :param src_flow: The name of the flow that created the message
    :type src_flow: str
    :param dst_flow: The name of the flow that should receive the message
    :type dst_flow: str
    :param created_by: The name of the flow that created the message
    :type created_by: str
    :param private_keys: A list of private keys that should not be serialized or logged
    :type private_keys: List[str], optional
    """

    def __init__(
        self,
        data_dict: Dict[str, Any],
        src_flow: str,
        dst_flow: str,
        created_by: str = None,
        private_keys: List[str] = None,
    ):

        created_by = src_flow if created_by is None else created_by
        super().__init__(data=data_dict, created_by=created_by, private_keys=private_keys)

        self.src_flow = src_flow
        self.dst_flow = dst_flow

    def to_string(self):
        """Returns a string representation of the message.

        :return: The string representation of the message.
        :rtype: str
        """
        src_flow = self.src_flow
        dst_flow = self.dst_flow

        message = (
            f"\n{colorama.Fore.GREEN} ~~~ InputMessage: `{src_flow}` --> `{dst_flow}` ~~~\n"
            f"{colorama.Fore.WHITE}{self.__str__()}{colorama.Style.RESET_ALL}"
        )

        return message

    @staticmethod
    def build(
        data_dict: Dict[str, Any],
        # ToDo: What does this offer over the constructor? If nothing, remove it and update the launcher.
        src_flow: str,
        dst_flow: str,
        private_keys: Optional[List[str]] = None,
        created_by: Optional[str] = None,
    ) -> "InputMessage":
        """Static method that builds an InputMessage object.

        :param data_dict: The data content of the message
        :type data_dict: Dict[str, Any]
        :param src_flow: The name of the flow that created the message
        :type src_flow: str
        :param dst_flow: The name of the flow that should receive the message
        :type dst_flow: str
        :param created_by: The name of the flow that created the message
        :type created_by: str
        :param private_keys: A list of private keys that should not be serialized or logged
        :type private_keys: List[str], optional
        :return: The built InputMessage object
        :rtype: InputMessage
        """

        if created_by is None:
            created_by = src_flow

        input_message = InputMessage(
            data_dict=data_dict, src_flow=src_flow, dst_flow=dst_flow, created_by=created_by, private_keys=private_keys
        )

        return input_message


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


@dataclass
class OutputMessage(Message):
    r"""This class represents an output message that is passed from one flow to another.

    :param src_flow: The name of the flow that created the message
    :type src_flow: str
    :param dst_flow: The name of the flow that should receive the message
    :type dst_flow: str
    :param output_data: The data content of the message
    :type output_data: Dict[str, Any]
    :param raw_response: The raw response of the message
    :type raw_response: Dict[str, Any]
    :param input_message_id: The unique identification of the input message
    :type input_message_id: str
    :param history: The history of the flow
    :type history: FlowHistory
    :param created_by: The name of the flow that created the message
    :type created_by: str
    :param \**kwargs: arguments that are passed to the Message constructor
    """

    def __init__(
        self,
        src_flow: str,
        dst_flow: str,
        # output_keys: List[str],
        output_data: Dict[str, Any],
        raw_response: Optional[Dict[str, Any]],
        # missing_output_keys: List[str],
        input_message_id: str,
        history: "FlowHistory",
        created_by: str,
        **kwargs,
    ):
        super().__init__(data={}, created_by=created_by, **kwargs)

        self.src_flow = src_flow
        self.dst_flow = dst_flow
        self.input_message_id = input_message_id
        # self.data["output_keys"] = output_keys
        # if missing_output_keys:
        #     self.data["missing_output_keys"] = missing_output_keys
        if raw_response is not None:
            self.data["raw_response"] = raw_response
        self.data["output_data"] = output_data
        self.history = history.to_list()

    def to_string(self):
        """Returns a string representation of the message.

        :return: The string representation of the message.
        :rtype: str
        """
        src_flow = self.src_flow
        dst_flow = self.dst_flow

        message = (
            f"\n{colorama.Fore.BLUE} ~~~ OutputMessage: `{src_flow}` --> `{dst_flow}` ~~~\n"
            f"{colorama.Fore.WHITE}{self.__str__()}{colorama.Style.RESET_ALL}"
        )

        return message

    def get_output_data(self):
        """Returns the output data of the message.

        :return: The output data of the message.
        :rtype: Dict[str, Any]
        """
        return self.data["output_data"]
