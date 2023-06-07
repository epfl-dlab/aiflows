from typing import List

from src.flows.abstract import AtomicFlow
from src.messages import InputMessage, TaskMessage


class FixedReplyAtomicFlow(AtomicFlow):
    def __init__(
        self,
        name: str,
        description: str,
        fixed_reply: str,
        expected_outputs: List[str] = None,
        expected_inputs: List[str] = None,
        verbose: bool = False
    ):
        if expected_outputs is None:
            expected_outputs = ["query"]

        super().__init__(
            name=name,
            description=description,
            expected_inputs=expected_inputs,
            expected_outputs=expected_outputs,
            verbose=verbose,
        )

        self.fixed_reply = fixed_reply

    def run(self, task_message: TaskMessage):
        key = self.state["expected_output_keys"][0]
        self._update_state({key: self.fixed_reply})
