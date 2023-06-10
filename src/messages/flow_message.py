from dataclasses import dataclass
from typing import List, Any, Union
import copy

from src.messages import Message


@dataclass
class TaskMessage(Message):
    expected_outputs: List[str]
    target_flow_run_id: str
    task_name: str

    def __init__(self, **kwargs):
        super(TaskMessage, self).__init__(**kwargs)
        self.expected_outputs = kwargs.pop("expected_outputs", [])
        self.target_flow_run_id = kwargs.pop("target_flow_run_id", None)
        self.task_name = kwargs.pop("task_name", "")

    def __repr__(self):
        extended = copy.deepcopy(self.data)
        extended["expected_outputs"] = self.expected_outputs
        return repr(extended)


@dataclass
class StateUpdateMessage(Message):
    updated_keys: List[str]

    def __init__(self, **kwargs):
        super(StateUpdateMessage, self).__init__(**kwargs)
        self.updated_keys = kwargs.pop("updated_keys", {})


@dataclass
class OutputMessage(Message):
    error_message: Union[None, str]
    history: Any

    def __init__(self, **kwargs):
        super(OutputMessage, self).__init__(**kwargs)
        self.error_message = kwargs.pop("error_message", None)

        from src.history import FlowHistory
        self.history: FlowHistory = kwargs.pop("history", FlowHistory())
