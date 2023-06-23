from typing import List, Dict, Any

from flows.base_flows import CompositeFlow
import flows.utils

log = flows.utils.get_pylogger(__name__)


class SequentialFlow(CompositeFlow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _validate_parameters(self, kwargs):
        # ToDo: Deal with this in a cleaner way (with less repetition)
        super()._validate_parameters(kwargs)

        if "subflows" not in kwargs:
            raise KeyError("Generator Critic needs a `subflows` parameter")

        assert len(kwargs["subflows"]) > 0, f"Sequential flow needs at least one flow, currently has 0"

    def run(self, input_data: Dict[str, Any], expected_outputs: List[str]) -> Dict[str, Any]:
        # ~~~ sets the input_data in the flow_state dict ~~~
        self._update_state(update_data=input_data)

        for current_flow in self.subflows.values():
            # ~~~ Execute the flow and update state with answer ~~~
            flow_answer = self._call_flow_from_state(
                flow=current_flow
            )
            self._update_state(flow_answer)

            # ~~~ Check whether we can exit already ~~~
            if self._early_exit():
                log.info(f"[{self.flow_config['name']}] End of interaction detected")
                break

        # ~~~ The final answer should be in self.flow_state, thus allow_class_namespace=False ~~~
        return self._get_keys_from_state(keys=expected_outputs, allow_class_namespace=False)
