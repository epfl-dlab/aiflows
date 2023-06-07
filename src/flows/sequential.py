from typing import List, Dict

from src.flows import CompositeFlow, Flow
from src.messages import TaskMessage
from src import utils

log = utils.get_pylogger(__name__)


class SequentialFlow(CompositeFlow):
    def __init__(
            self,
            name: str,
            description: str,
            expected_inputs: List[str],
            expected_outputs: List[str],
            flows: Dict[str, Flow],
            early_exit_key: str = None,
            verbose: bool = False
    ):
        super().__init__(
            name=name,
            description=description,
            expected_inputs=expected_inputs,
            expected_outputs=expected_outputs,
            flows=flows,
            verbose=verbose
        )

        assert len(flows) > 0, f"Sequential flow needs at least one flow, currently has {len(flows)}"

        self.ordered_flows = list(self.flows.keys())
        self.early_exit_key = early_exit_key

    def _early_exit(self):
        if self.early_exit_key:
            if self.early_exit_key in self.state:
                return bool(self.state[self.early_exit_key].content)
        return False

    def run(self, task_message: TaskMessage):
        api_key = self.state["api_key"]
        _parents = [task_message.message_id]

        for current_flow_id in self.ordered_flows:
            current_flow = self.flows[current_flow_id]
            current_flow.initialize()
            current_flow.set_api_key(api_key=api_key)

            flow_answer = self._call_flow(flow_id=current_flow_id,
                                          parent_message_ids=_parents)
            self._update_state(flow_answer)

            if self._early_exit():
                log.info("Early end of sequential flow detected")
                break

            _parents = [flow_answer.message_id]
