from dataclasses import dataclass
from typing import Dict, Any

from src.messages import FlowMessage, Message


@dataclass
class InputMessage(FlowMessage):
    """
    The InputMessage class is a special kind of FlowMessage that represents an input message to a flow.
    It contains a dictionary of input messages, where the values are themselves messages.

    Attributes:
        inputs (Dict[str, Message]): A dictionary containing input messages.
            The keys are the input names, and the values are Message
        target_flow (str): the flow_run_id to which the message is sent
    """

    inputs: Dict[str, Message]
    target_flow: str

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.message_type = "input-message"


@dataclass
class OutputMessage(FlowMessage):
    """
    The OutputMessage class is a special kind of FlowMessage that represents an output message from a flow.
    It contains a dictionary of parsed_outputs, where the values are themselves messages.

    Attributes:
        parsed_outputs (Dict[str, Message]): A dictionary containing output messages.
            The keys are the output key names, and the values are Message
        valid_parsing (str): a boolean indicating whether the parsed_outputs contains the expected keys
        message_creation_history (FlowHistory): The history that lead to the creation of this OutputMessage in the flow.
    """
    parsed_outputs: Dict[str, FlowMessage]
    valid_parsing: bool
    message_creation_history: Any

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.message_type = "output-message"

        if "message_creation_history" not in kwargs:
            from src.history import FlowHistory
            self.message_creation_history = FlowHistory()

    def to_dict(self) -> Dict:
        """
        Converts the `OutputMessage` instance to a dictionary representation.

        Returns:
            dict: A dictionary representation of the `OutputMessage` instance.
        """
        d = self.__dict__

        if self.parsed_outputs is not None:
            d["parsed_outputs"] = {k: v.to_dict() for k, v in self.parsed_outputs.items()}

        if self.message_creation_history is not None:
            d["message_creation_history"] = self.message_creation_history.to_dict()

        return d
