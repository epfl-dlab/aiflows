import copy
import json
from dataclasses import dataclass
from typing import List, Any, Dict
import colorama

from flows.utils.general_helpers import create_unique_id, get_current_datetime_ns

colorama.init()


@dataclass
class Message:
    # ~~~ Message unique identification ~~~
    message_id: str
    created_at: str

    # ~~~ Contextual information about the message ~~~
    created_by: str
    message_type: str

    # ~~~ Data content ~~~
    data: Dict[str, Any]

    # ~~~ Private keys that should not be serialized or logged ~~~
    private_keys: List[str]

    def __init__(self, **kwargs):
        kwargs = copy.deepcopy(kwargs)

        # ~~~ Initialize message identifiers ~~~
        self.message_id = create_unique_id()
        self.created_at = get_current_datetime_ns()

        # ~~~ Initialize contextual information ~~~
        assert "message_type" not in kwargs, "message_type should not be passed as a keyword argument"
        self.message_type = self.__class__.__name__
        self.created_by = kwargs.pop("created_by")

        # ~~~ Initialize Data content ~~~
        self.data = kwargs.pop("data", {})

        # ~~~ Initialize private keys ~~~
        self.private_keys = []
        if kwargs.get("private_keys", False):
            self.private_keys = kwargs.pop("private_keys")
        if "api_keys" not in self.private_keys:
            self.private_keys.append("api_keys")

    def __sanitized__dict__(self):
        """Removes any private_keys potentially present in the __dict__ object or the data dictionary"""
        __sanitized__dict__ = copy.deepcopy(self.__dict__)
        for private_key in self.private_keys:
            if private_key in __sanitized__dict__:
                del __sanitized__dict__[private_key]

        for private_key in self.private_keys:
            if private_key in __sanitized__dict__["data"]:
                del __sanitized__dict__["data"][private_key]

        del __sanitized__dict__["private_keys"]
        return __sanitized__dict__

    def to_dict(self):
        d = self.__sanitized__dict__()
        return d

    def to_string(self):
        """Returns a formatted string representation of the message that will be logged to the console"""
        raise NotImplementedError()

    def __str__(self):
        d = self.__sanitized__dict__()
        return json.dumps(d, indent=4)

    def __repr__(self):
        # ToDo: Note that created_at and message_id are currently included in the __repr__.
        #   Do we want to exclude them?
        # ToDo: Might be useful to override __setstate__ and soft_copy the message to get a fresh created_at
        #  when reading history?
        #   See code below

        return self.__str__()

    # def to_string(self, colored: bool = True) -> str:
    #     role = f"[{self.message_id} -- {self.flow_run_id}] {self.message_creator} ({self.flow_runner})"
    #     content = self.__str__()
    #
    #     if colored:
    #         return f"{colorama.Fore.BLUE}~~ {role} ~~\n{colorama.Fore.GREEN}{content}{colorama.Style.RESET_ALL}"
    #     return f" ~~ {role} ~~\n{content}"
    #
    #
    # def soft_copy(self, fields_to_ignore: List[str] = None) -> Dict:
    #     """
    #     Creates a soft copy of a Message object, while ignoring fields that should be unique to each message
    #
    #     Args:
    #         fields_to_ignore (List[str], optional): A list of attribute names to ignore in the copied object.
    #             Defaults to ["message_id", "created_at", "message_index"].
    #
    #     Returns:
    #         dict: A dictionary representing the copied Message object.
    #     """
    #
    #     # ~~~ By default, ignore unique identifiers from soft copy ~~~
    #     if fields_to_ignore is None:
    #         fields_to_ignore = ["message_id", "created_at"]
    #
    #     # ~~~ Deepcopy the content ~~~
    #     d = copy.deepcopy(self.__dict__)
    #     for key in fields_to_ignore:
    #         del d[key]
    #
    #     d["parent_message_ids"] = [self.message_id]
    #     return d
