import copy
import pprint
from dataclasses import dataclass
from typing import List, Any, Dict
import colorama

from src.utils.general_helpers import create_unique_id, get_current_datetime_ns

DEFAULT_CREATOR = "Executor"
DEFAULT_FLOW_RUNNER = "Execute-runner"

colorama.init()


@dataclass
class Message:
    # ~~~ Message unique identification ~~~
    message_id: str
    created_at: str

    # ~~~ Contextual information about the message ~~~
    message_creator: str
    parent_message_ids: List[str]
    flow_runner: str
    flow_run_id: str

    # ~~~ Data content ~~~
    data: Dict[str, Any]

    def __init__(self, **kwargs):
        # ~~~ Initialize message identifiers ~~~
        self.message_id = create_unique_id()
        self.created_at = get_current_datetime_ns()

        # ~~~ Initialize contextual information ~~~
        self.message_creator = kwargs.pop("message_creator", DEFAULT_CREATOR)
        self.parent_message_ids = kwargs.pop("parent_message_ids", [])
        self.flow_runner = kwargs.pop("flow_runner", DEFAULT_FLOW_RUNNER)
        self.flow_run_id = kwargs.pop("flow_run_id", create_unique_id())

        # ~~~ Initialize Data content
        self.data = kwargs.pop("data", {})

    def __str__(self):
        d = self.__dict__
        return pprint.pformat(d, indent=4)

    def to_dict(self):
        return self.__dict__

    def to_string(self, colored: bool = True) -> str:
        role = f"[{self.message_id} -- {self.flow_run_id}] {self.message_creator} ({self.flow_runner})"
        content = self.__str__()

        if colored:
            return f"{colorama.Fore.BLUE}~~ {role} ~~\n{colorama.Fore.GREEN}{content}{colorama.Style.RESET_ALL}"
        return f" ~~ {role} ~~\n{content}"


    def soft_copy(self, fields_to_ignore: List[str] = None) -> Dict:
        """
        Creates a soft copy of a Message object, while ignoring fields that should be unique to each message

        Args:
            fields_to_ignore (List[str], optional): A list of attribute names to ignore in the copied object.
                Defaults to ["message_id", "created_at", "message_index"].

        Returns:
            dict: A dictionary representing the copied Message object.
        """

        # ~~~ By default, ignore unique identifiers from soft copy ~~~
        if fields_to_ignore is None:
            fields_to_ignore = ["message_id", "created_at"]

        # ~~~ Deepcopy the content ~~~
        d = copy.deepcopy(self.__dict__)
        for key in fields_to_ignore:
            del d[key]

        d["parent_message_ids"] = [self.message_id]
        return d