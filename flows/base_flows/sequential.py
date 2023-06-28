import pdb
from typing import List, Dict, Any, Optional

from flows.base_flows import CompositeFlow
import flows.utils

log = flows.utils.get_pylogger(__name__)


class SequentialFlow(CompositeFlow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @classmethod
    def _validate_parameters(cls, kwargs):
        # ToDo: Deal with this in a cleaner way (with less repetition)
        cls.__base__._validate_parameters(kwargs)

        if "subflows" not in kwargs:
            raise KeyError("Generator Critic needs a `subflows` parameter")

        assert len(kwargs["subflows"]) > 0, f"Sequential flow needs at least one flow, currently has 0"

    def run(self,
            input_data: Dict[str, Any],
            private_keys: Optional[List[str]] = [],
            keys_to_ignore_for_hash: Optional[List[str]] = []) -> Dict[str, Any]:

        self._state_update_dict(update_data=input_data)

        for current_flow in self.subflows.values():
            # ~~~ Execute the flow and update state with answer ~~~
            flow_answer = self._call_flow_from_state(
                flow_to_call=current_flow, private_keys=private_keys, keys_to_ignore_for_hash=keys_to_ignore_for_hash
            )
            # self._update_state(flow_answer)
            self._state_update_dict(update_data=flow_answer)

            # ~~~ Check whether we can exit already ~~~
            if self._early_exit():
                log.info(f"[{self.flow_config['name']}] End of interaction detected")
                break

        # ~~~ The final answer should be in self.flow_state, thus allow_class_attributes=False ~~~
        # self._state_update_dict(flow_answer)

        # ~~~ The final answer should be in self.flow_state, thus allow_class_attributes=False ~~~
        outputs = self._fetch_state_attributes_by_keys(keys=input_data["output_keys"],
                                                       allow_class_attributes=False)

        return outputs


