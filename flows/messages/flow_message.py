from dataclasses import dataclass
from typing import List, Any, Dict, Optional
import colorama

from flows.messages import Message

colorama.init()


@dataclass
class InputMessage(Message):
    def __init__(self,
                 src_flow: str,
                 dst_flow: str,
                 output_keys: List[str],
                 api_keys: Optional[Dict[str, str]] = None,
                 keys_to_ignore_for_hash: Optional[List[str]] = None,
                 **kwargs):
        super().__init__(**kwargs)

        self.data["src_flow"] = src_flow
        self.data["dst_flow"] = dst_flow
        self.data["output_keys"] = output_keys
        if api_keys:
            self.data["api_keys"] = api_keys

        # ~~~ Initialize keys to ignore for hash ~~~
        self.keys_to_ignore_for_hash = []
        if keys_to_ignore_for_hash:
            self.keys_to_ignore_for_hash = keys_to_ignore_for_hash
        if "api_keys" not in self.keys_to_ignore_for_hash:
            self.keys_to_ignore_for_hash.append("api_keys")

    def to_string(self):
        src_flow = self.data["src_flow"]
        dst_flow = self.data["dst_flow"]

        message = f"\n{colorama.Fore.GREEN} ~~~ InputMessage: `{src_flow}` --> `{dst_flow}` ~~~\n" \
                  f"{colorama.Fore.WHITE}{self.__str__()}{colorama.Style.RESET_ALL}"

        return message


@dataclass
class UpdateMessage_Generic(Message):
    def __init__(self,
                 updated_flow: str,
                 **kwargs):
        super().__init__(**kwargs)
        self.data["updated_flow"] = updated_flow

    def to_string(self):
        updated_flow = self.data["updated_flow"]

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

        super().__init__(updated_flow=updated_flow, **kwargs)
        self.data["role"] = role
        self.data["content"] = content

    def to_string(self):
        updated_flow = self.data["updated_flow"]
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
        self.data["updated_flow"] = updated_flow
        self.data["keys_deleted_from_namespace"] = keys_deleted_from_namespace

    def to_string(self):
        updated_flow = self.data["updated_flow"]

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
        self.data["updated_flow"] = updated_flow
        self.data["keys_deleted_from_namespace"] = keys_deleted_from_namespace

    def to_string(self):
        updated_flow = self.data["updated_flow"]

        message = f"\n{colorama.Fore.CYAN} ~~~ ResetMessageFull ({self.__class__.__name__}): `{updated_flow}` ~~~\n" \
                  f"{colorama.Fore.WHITE}{self.__str__()}{colorama.Style.RESET_ALL}"

        return message


@dataclass
class OutputMessage(Message):
    def __init__(self,
                 src_flow: str,
                 dst_flow: str,
                 output_keys: List[str],
                 output_data: Dict[str, Any],
                 missing_output_keys: List[str],
                 history: 'FlowHistory',
                 **kwargs):
        super().__init__(**kwargs)

        self.data["src_flow"] = src_flow
        self.data["dst_flow"] = dst_flow
        self.data["output_keys"] = output_keys
        self.data["output_data"] = output_data
        self.data["missing_output_keys"] = missing_output_keys
        self.history = history.to_list()

    def to_string(self):
        src_flow = self.data["src_flow"]
        dst_flow = self.data["dst_flow"]

        message = f"\n{colorama.Fore.BLUE} ~~~ OutputMessage: `{src_flow}` --> `{dst_flow}` ~~~\n" \
                  f"{colorama.Fore.WHITE}{self.__str__()}{colorama.Style.RESET_ALL}"

        return message
