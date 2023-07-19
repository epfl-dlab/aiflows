from typing import List, Dict, Any, Optional

from flows.base_flows.abstract import AtomicFlow


class FixedReplyFlow(AtomicFlow):
    REQUIRED_KEYS_CONFIG = ["fixed_reply"]
    REQUIRED_KEYS_CONSTRUCTOR = []

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def run(self,
            input_data: Dict[str, Any]) -> Dict[str, Any]:

        return {"fixed_reply": self.flow_config["fixed_reply"]}

