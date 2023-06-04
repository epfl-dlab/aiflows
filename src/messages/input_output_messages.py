from dataclasses import dataclass
from typing import Dict, Any

from src.messages import FlowMessage, Message

@dataclass
class InputMessage(FlowMessage):
    inputs: Dict[str, Message]
    target_flow: str

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.message_type = "input-message"

@dataclass
class OutputMessage(FlowMessage):
    parsed_outputs: Dict[str, FlowMessage]
    valid_parsing: bool
    message_creation_history: Any

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.message_type = "output-message"

        from src.history import FlowHistory
        self.message_creation_history = FlowHistory()

    def to_dict(self):
        d = self.__dict__

        if self.parsed_outputs is not None:
            d["parsed_outputs"] = {k: v.to_dict() for k, v in self.parsed_outputs.items()}

        if self.message_creation_history is not None:
            d["message_creation_history"] = self.message_creation_history.to_dict()

        return d
