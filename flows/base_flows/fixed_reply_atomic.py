from typing import List, Dict, Any

from flows.base_flows.abstract import AtomicFlow


class FixedReplyAtomicFlow(AtomicFlow):
    def __init__(self, **kwargs):
        self._validate_parameters(kwargs)
        super().__init__(**kwargs)

    @classmethod
    def _validate_parameters(cls, kwargs):
        # ToDo: Deal with this in a cleaner way (with less repetition)
        super()._validate_parameters(kwargs)

        if "fixed_reply" not in kwargs["flow_config"]:
            raise KeyError("FixedReplyAtomicFlow needs a `fixed_reply` parameter")

    def run(self, input_data: Dict[str, Any], expected_outputs: List[str]) -> Dict[str, Any]:
        key = expected_outputs[0]
        return {key: self.flow_config["fixed_reply"]}

