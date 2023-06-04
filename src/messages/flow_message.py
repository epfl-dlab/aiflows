import copy
from dataclasses import dataclass
from typing import Dict, ClassVar

from src.messages import Message

import colorama

from src.utils.general_helpers import create_unique_id

colorama.init()


@dataclass
class FlowMessage(Message):
    """
    FlowMessage class represents messages that are produced and exchanged by flows.
    It inherits from the Message class and adds additional specific attributes.

    Attributes:
        flow_runner (str): The name of the flow that was running when producing the message.
        flow_run_id (str): The ID of the flow that was running when producing the message.
        message_index (int): The index of the message.
    From Message:
        message_id (str): The unique identifier of the message.
        message_creator (str): The creator of the message.
        content (Any): The content of the message.
        created_at (str): The timestamp indicating when the message was created.
        message_type (str): The type of the message.
        parents (List[str]): The list of parent message IDs.

    Methods:
        to_string(self, show_dict=False): Returns a string representation of the FlowMessage.

    """
    flow_runner: str
    flow_run_id: str
    message_index: int

    count: ClassVar[int] = 0

    def __init__(self, **kwargs):
        super().__init__()

        kwargs = copy.deepcopy(kwargs)
        self.__dict__.update(kwargs)

        if "parents" not in kwargs:
            self.parents = []

        if "message_id" not in kwargs:
            self.message_id = create_unique_id()

        if "flow_run_id" not in kwargs:
            self.flow_run_id = create_unique_id()

        self.message_type = "flow-message"

        self.message_index = self.count
        FlowMessage.count += 1

    def to_string(self, show_dict: bool = False) -> str:
        """
        Returns a string representation of the FlowMessage.

        Args:
            show_dict (bool): Whether to show the attributes as a dictionary or just the content

        Returns:
            str: The string representation of the FlowMessage.
        """

        role = f"[{self.message_id} -- {self.flow_run_id}] {self.message_creator} ({self.flow_runner})"
        if show_dict:
            content = self.__str__()
        else:
            content = str(self.content)

        return f"{colorama.Fore.BLUE}~~ {role} ~~\n{colorama.Fore.GREEN}{content}{colorama.Style.RESET_ALL}"


@dataclass
class FlowUpdateMessage(FlowMessage):
    """
    FlowUpdateMessage class represents an update message produced by a flow.
    It inherits from the FlowMessage class and adds the attribute corresponding to the state of the flow,
    at the moment of the message creation.

    Attributes:
        current_flow_state (Dict): The state of the flow that created the message at the moment of the message creation.
    """
    current_flow_state: Dict

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.message_type = "flow-update-message"
