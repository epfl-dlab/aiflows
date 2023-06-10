from typing import List, Dict, Any

from flows.base_flows.abstract import AtomicFlow


class FixedReplyAtomicFlow(AtomicFlow):
    fixed_reply: str

    def __init__(self, **kwargs):
        if "fixed_reply" not in kwargs:
            raise KeyError

        super().__init__(**kwargs)

        if self.expected_outputs is None:
            self.expected_outputs = ["query"]

    def run(self, input_data: Dict[str, Any], expected_outputs: List[str]) -> Dict[str, Any]:
        key = expected_outputs[0]
        return {key: self.fixed_reply}
