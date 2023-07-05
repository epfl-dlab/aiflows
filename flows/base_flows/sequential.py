from typing import List, Dict, Any, Optional

from flows.base_flows import CompositeFlow
from flows.utils.general_helpers import validate_parameters
from ..utils import logging

log = logging.get_logger(__name__)

# ToDo: Add support for multiple runs (c.f. generator_critic.py)


class SequentialFlow(CompositeFlow):
    REQUIRED_KEYS_CONSTRUCTOR = ["subflows"]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @classmethod
    def _validate_parameters(cls, kwargs):
        validate_parameters(cls, kwargs)

        assert len(kwargs["subflows"]) > 0, f"Sequential flow needs at least one flow, currently has 0"

    def run(self,
            input_data: Dict[str, Any],
            private_keys: Optional[List[str]] = [],
            keys_to_ignore_for_hash: Optional[List[str]] = []) -> Dict[str, Any]:
        # ~~~ sets the input_data in the flow_state dict ~~~
        self._state_update_dict(update_data=input_data)

        for current_flow in self.subflows.values():
            # ~~~ Execute the flow and update state with answer ~~~
            output_message = self._call_flow_from_state(
                flow_to_call=current_flow, private_keys=private_keys, keys_to_ignore_for_hash=keys_to_ignore_for_hash
            )
            self._state_update_dict(update_data=output_message)

            # ~~~ Check for end of interaction
            if self._early_exit():
                log.info(f"[{self.flow_config['name']}] End of interaction detected")
                break

        # ~~~ The final answer should be in self.flow_state, thus allow_class_attributes=False ~~~
        outputs = self._fetch_state_attributes_by_keys(keys=input_data["output_keys"],
                                                       allow_class_attributes=False)

        return outputs

    @classmethod
    def type(cls):
        return "sequential"


