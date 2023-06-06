from dataclasses import dataclass
from typing import List, Any, Union, Dict

from src.messages import Message


@dataclass
class TaskMessage(Message):
    expected_output_keys: List[str]

    def __int__(self, **kwargs):
        super(TaskMessage, self).__init__(**kwargs)
        self.expected_output_keys = kwargs.pop("expected_output_keys", [])


@dataclass
class StateUpdateMessage(Message):
    updates: Dict[str, Any]

    def __init__(self, **kwargs):
        super(StateUpdateMessage, self).__init__(**kwargs)
        self.updates = kwargs.pop("updates", {})


@dataclass
class OutputMessage(Message):
    error_message: Union[None, str]
    history: Any

    def __init__(self, **kwargs):
        super(OutputMessage, self).__init__(**kwargs)
        self.error_message = kwargs.pop("error_message", None)

        from src.history import FlowHistory
        self.history: FlowHistory = kwargs.pop("history", FlowHistory())
