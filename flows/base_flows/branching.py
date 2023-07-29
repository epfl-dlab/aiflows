from typing import List, Dict, Any, Optional, Tuple

from flows.base_flows import CompositeFlow, Flow
from ..utils import logging
from flows.utils.general_helpers import validate_parameters

log = logging.get_logger(__name__)


class BranchingFlow(CompositeFlow):

    __default_flow_config = {
        "input_keys": ["branch", "branch_input_data"],
        "output_keys": ["branch_output_data"]
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get_input_keys(self) -> List[str]:
        return ["branch", "branch_input_data"]
    
    def get_output_keys(self) -> List[str]:
        return ["branch_output_data"]
    
    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        branch = input_data["branch"]
        branch_input_data = input_data["branch_input_data"]
        self._state_update_dict({"branch": branch})
        self._state_update_dict(branch_input_data)

        current_flow = self._get_subflow(branch)
        if current_flow is None:
            raise ValueError(f"Branching flow has no subflow with name {branch}")
        # ~~~ Execute the flow and update state with answer ~~~
        output_message = self._call_flow_from_state(
            flow_to_call=current_flow
        )
       
        return {"branch_output_data": output_message.data["output_data"]}

    @classmethod
    def type(cls):
        return "branching"