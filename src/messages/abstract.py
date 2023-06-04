import copy
import pprint
from dataclasses import dataclass
from typing import List, Any


from src.utils.general_helpers import create_unique_id, get_current_datetime_ns


@dataclass
class Message:
    message_id: str
    message_creator: str
    content: Any
    created_at: str
    message_type: str
    parents: List[str]

    def __init__(self):
        self.message_id = create_unique_id()
        self.created_at = get_current_datetime_ns()
        self.message_type = "message"

    def __str__(self):
        d = self.__dict__
        return pprint.pformat(d, indent=4)

    def to_dict(self):
        return self.__dict__

    def soft_copy(self, fields_to_ignore: List[str] = None):
        if fields_to_ignore is None:
            fields_to_ignore = ["message_id", "created_at", "message_index"]

        d = copy.deepcopy(self.__dict__)
        for key in fields_to_ignore:
            del d[key]

        if "parents" in d:
            d["parents"] = [self.message_id]

        return d

    def to_string(self, **kwargs):
        return self.__str__()

