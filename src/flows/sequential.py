from typing import List, Dict, Any

from src.flows import CompositeFlow
from src import utils

log = utils.get_pylogger(__name__)


class SequentialFlow(CompositeFlow):
    ordered_flows: List

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        flows = self.flow_config["flows"]
        assert len(flows) > 0, f"Sequential flow needs at least one flow, currently has {len(flows)}"

        self.ordered_flows = list(flows.keys())

    def run(self, input_data: Dict[str, Any], expected_outputs: List[str]) -> Dict[str, Any]:
        self._update_state(input_data)

        for current_flow_id in self.ordered_flows:
            # ~~~ Initialize flow ~~~
            current_flow = self._init_flow(self.flows[current_flow_id])

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
