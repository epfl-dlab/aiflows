from dataclasses import dataclass
from typing import List, Any, Dict, Optional
import colorama

from flows.messages import Message

colorama.init()


# ToDo: When logging the "\n" in the nested messages is not mapped to a new line which makes it hard to debug. Fix that.


@dataclass
class InputMessage(Message):

    def __init__(self,
                 data_dict: Dict[str, Any],
                 src_flow: str,
                 dst_flow: str,
                 created_by: str = None,
                 private_keys: List[str] = None,
                 keys_to_ignore_for_hash: Optional[
                     List[str]] = None):  # TODO(yeeef): remove keys_to_ignore_for_hash from InputMessage

        created_by = src_flow if created_by is None else created_by
        super().__init__(data=data_dict, created_by=created_by, private_keys=private_keys)

        self.src_flow = src_flow
        self.dst_flow = dst_flow

        # ~~~ Initialize keys to ignore for hash ~~~
        self.keys_to_ignore_for_hash = []
        if keys_to_ignore_for_hash:
            self.keys_to_ignore_for_hash = keys_to_ignore_for_hash

    def to_string(self):
        src_flow = self.src_flow
        dst_flow = self.dst_flow

        message = f"\n{colorama.Fore.GREEN} ~~~ InputMessage: `{src_flow}` --> `{dst_flow}` ~~~\n" \
                  f"{colorama.Fore.WHITE}{self.__str__()}{colorama.Style.RESET_ALL}"

        return message

    @staticmethod
    def build(data_dict: Dict[str, Any],
              # ToDo: What does this offer over the constructor? If nothing, remove it and update the launcher.
              src_flow: str,
              dst_flow: str,
              private_keys: Optional[List[str]] = None,
              created_by: Optional[str] = None) -> 'InputMessage':

        if created_by is None:
            created_by = src_flow

        input_message = InputMessage(
            data_dict=data_dict,
            src_flow=src_flow,
            dst_flow=dst_flow,
            created_by=created_by,
            private_keys=private_keys
        )

        return input_message


@dataclass
class UpdateMessage_Generic(Message):
    def __init__(self,
                 updated_flow: str,
                 **kwargs):
        super().__init__(**kwargs)
        self.updated_flow = updated_flow

    def to_string(self):
        updated_flow = self.updated_flow

        message = f"\n{colorama.Fore.MAGENTA} ~~~ UpdateMessage ({self.__class__.__name__}): `{updated_flow}` ~~~\n" \
                  f"{colorama.Fore.WHITE}{self.__str__()}{colorama.Style.RESET_ALL}"

        return message


@dataclass
class UpdateMessage_ChatMessage(UpdateMessage_Generic):
    def __init__(self,
                 content: str,
                 role: str,
                 updated_flow: str,
                 **kwargs):
        super().__init__(data={}, updated_flow=updated_flow, **kwargs)
        self.data["role"] = role
        self.data["content"] = content

    def to_string(self):
        updated_flow = self.updated_flow
        role = self.data["role"]
        color = colorama.Fore.RED if role == "assistant" else colorama.Fore.YELLOW

        message = f"\n{color} ~~~ UpdateMessage ({self.__class__.__name__}): " \
                  f"`{updated_flow}` (role: {role}) ~~~\n" \
                  f"{colorama.Fore.WHITE}{self.__str__()}{colorama.Style.RESET_ALL}"

        return message


@dataclass
class UpdateMessage_NamespaceReset(Message):
    def __init__(self,
                 updated_flow: str,
                 created_by: str,
                 keys_deleted_from_namespace: List[str]):
        super().__init__(created_by=created_by, data={})
        self.updated_flow = updated_flow
        self.data["keys_deleted_from_namespace"] = keys_deleted_from_namespace

    def to_string(self):
        updated_flow = self.updated_flow

        message = f"\n{colorama.Fore.CYAN} ~~~ ResetMessageNamespaceOnly ({self.__class__.__name__}): `{updated_flow}` ~~~\n" \
                  f"{colorama.Fore.WHITE}{self.__str__()}{colorama.Style.RESET_ALL}"

        return message


@dataclass
class UpdateMessage_FullReset(Message):
    def __init__(self,
                 updated_flow: str,
                 created_by: str,
                 keys_deleted_from_namespace: List[str]):
        super().__init__(created_by=created_by, data={})
        self.updated_flow = updated_flow
        self.data["keys_deleted_from_namespace"] = keys_deleted_from_namespace

    def to_string(self):
        updated_flow = self.updated_flow

        message = f"\n{colorama.Fore.CYAN} ~~~ ResetMessageFull ({self.__class__.__name__}): `{updated_flow}` ~~~\n" \
                  f"{colorama.Fore.WHITE}{self.__str__()}{colorama.Style.RESET_ALL}"

        return message


@dataclass
class OutputMessage(Message):
    def __init__(self,
                 src_flow: str,
                 dst_flow: str,
                 # output_keys: List[str],
                 output_data: Dict[str, Any],
                 raw_response: Optional[Dict[str, Any]],
                 # missing_output_keys: List[str],
                 input_message_id: str,
                 history: 'FlowHistory',
                 created_by: str,
                 **kwargs):
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
        src_flow = self.src_flow
        dst_flow = self.dst_flow

        message = f"\n{colorama.Fore.BLUE} ~~~ OutputMessage: `{src_flow}` --> `{dst_flow}` ~~~\n" \
                  f"{colorama.Fore.WHITE}{self.__str__()}{colorama.Style.RESET_ALL}"

        return message

    def get_output_data(self):
        return self.data["output_data"]
