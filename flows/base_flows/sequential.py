from typing import List, Dict, Any

from flows.base_flows import CompositeFlow
import flows.utils

log = flows.utils.get_pylogger(__name__)


class SequentialFlow(CompositeFlow):
    ordered_flows: List

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        _flows = self.flow_config["flows"]
        assert len(_flows) > 0, f"Sequential flow needs at least one flow, currently has {len(_flows)}"

        # ToDo: using a dictionary for flows might not ensure the order of the flows
        if isinstance(_flows, dict):
            _flows = list(_flows.values())
        assert isinstance(_flows, list), f"Sequential flow needs a list of flows, currently has {type(_flows)}"
        self.ordered_flows = _flows

    def run(self, input_data: Dict[str, Any], expected_outputs: List[str]) -> Dict[str, Any]:
        self._update_state(input_data)

        for flow in self.ordered_flows:
            # ~~~ Initialize flow ~~~
            current_flow = self._init_flow(flow)

            # ~~~ Execute the flow and update state with answer ~~~
            flow_answer = self._call_flow_from_state(
                flow=current_flow
            )
            self._update_state(flow_answer)

            # ~~~ Check whether we can exit already ~~~
            if self._early_exit():
                log.info("Early end of sequential flow detected")
                break

        # ~~~ The final answer should be in self.flow_state, thus allow_class_namespace=False ~~~
        return self._get_keys_from_state(keys=expected_outputs, allow_class_namespace=False)
