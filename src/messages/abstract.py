import copy
import pprint
from dataclasses import dataclass
from typing import List, Any, Dict

from src.utils.general_helpers import create_unique_id, get_current_datetime_ns


@dataclass
class Message:
    """
    Represents the base message with attributes expected from any message.

    Attributes:
        message_id (str): The unique identifier of the message.
        message_creator (str): The creator of the message.
        content (Any): The content of the message.
        created_at (str): The timestamp indicating when the message was created.
        message_type (str): The type of the message.
        parents (List[str]): The list of parent message IDs.

    Methods:
        to_dict(): Converts the Message object to a dictionary representation.
        soft_copy(fields_to_ignore: List[str] = None): Creates a soft copy of the Message object.
    """

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

    def soft_copy(self, fields_to_ignore: List[str] = None) -> Dict:
        """
        Creates a soft copy of a Message object, while ignoring fields that should be unique to each message

        Args:
            fields_to_ignore (List[str], optional): A list of attribute names to ignore in the copied object.
                Defaults to ["message_id", "created_at", "message_index"].

        Returns:
            dict: A dictionary representing the copied Message object.
        """
        if fields_to_ignore is None:
            fields_to_ignore = ["message_id", "created_at", "message_index"]

        d = copy.deepcopy(self.__dict__)
        for key in fields_to_ignore:
            del d[key]

        if "parents" in d:
            d["parents"] = [self.message_id]

        return d

