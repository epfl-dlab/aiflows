import copy
from dataclasses import dataclass
from typing import Dict, ClassVar

from src.messages import Message

import colorama

from src.utils.general_helpers import create_unique_id

colorama.init()


@dataclass
class FlowMessage(Message):
    flow_runner: str
    flow_run_id: str
    message_index: int

    count: ClassVar[int] = 0

    def __init__(self, **kwargs):
        super().__init__()

        kwargs = copy.deepcopy(kwargs)

        if "parents" not in kwargs:
            self.parents = []

        if "message_id" not in kwargs:
            self.message_id = create_unique_id()

        if "flow_run_id" not in kwargs:
            self.flow_run_id = create_unique_id()

        self.message_type = "flow-message"

        self.message_index = self.count
        self.__dict__.update(kwargs)
        FlowMessage.count += 1

    def to_string(self, show_dict=False):
        role = f"[{self.message_id} -- {self.flow_run_id}] {self.message_creator} ({self.flow_runner})"
        if show_dict:
            content = self.__str__()
        else:
            content = self.content

        return f"{colorama.Fore.BLUE}~~ {role} ~~\n{colorama.Fore.GREEN}{content}{colorama.Style.RESET_ALL}"

@dataclass
class FlowUpdateMessage(FlowMessage):
    current_flow_state: Dict

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.message_type = "flow-update-message"


