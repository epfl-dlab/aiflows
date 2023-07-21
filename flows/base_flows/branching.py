from typing import List, Dict, Any, Optional, Tuple

from flows.base_flows import CompositeFlow, Flow
from ..utils import logging
from flows.utils.general_helpers import validate_parameters

log = logging.get_logger(__name__)


class BranchingFlow(CompositeFlow):
    """
    A composite flow that branches to one of its subflows based on the branch value in the input_data.
    Input data should have a key called "branch" with the name of the subflow to call.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        # ~~~ sets the input_data in the flow_state dict ~~~
        self._state_update_dict(update_data=input_data)
        branch = input_data.get("branch", None)
        if branch is None:
            raise ValueError("Branching flow needs a branch key in the input_data")
        current_flow = self._get_subflow(branch)
        if current_flow is None:
            print(f"Branching flow has subflows: {self.subflows}")
            raise ValueError(f"Branching flow has no subflow with name {branch}")
        # ~~~ Execute the flow and update state with answer ~~~
        output_message = self._call_flow_from_state(
            flow_to_call=current_flow
        )
        self._state_update_dict(update_data=output_message)

        # ~~~ The final answer should be in self.flow_state, thus allow_class_attributes=False ~~~
        outputs = self._fetch_state_attributes_by_keys(keys=output_message.data["output_keys"],
                                                         allow_class_attributes=False)

        return outputs

    @classmethod
    def type(cls):
        return "branching"