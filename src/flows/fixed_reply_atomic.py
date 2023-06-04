from typing import List

from src.flows.abstract import AtomicFlow
from src.messages import InputMessage


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

    def _flow(self, expected_outputs: List[str], input_message: InputMessage = None):
        response = self.fixed_reply
        assert len(expected_outputs) == 1, "{self.name} can only produce one output."

        expected_key = expected_outputs[0]
        parsed_outputs = {expected_key: self._log_update(content=response)}
        return parsed_outputs
