from typing import List, Dict, Any, Optional

from flows.base_flows.abstract import AtomicFlow
from flows.utils.general_helpers import validate_parameters


class FixedReplyAtomicFlow(AtomicFlow):
    REQUIRED_KEYS_CONFIG = ["fixed_reply"]
    REQUIRED_KEYS_KWARGS = []

    def __init__(self, **kwargs):
        self._validate_parameters(kwargs)
        super().__init__(**kwargs)

    @classmethod
    def _validate_parameters(cls, kwargs):
        validate_parameters(cls, kwargs)

    def run(self,
            input_data: Dict[str, Any],
            private_keys: Optional[List[str]] = [],
            keys_to_ignore_for_hash: Optional[List[str]] = []) -> Dict[str, Any]:

        return {"raw_response": self.flow_config["fixed_reply"]}

