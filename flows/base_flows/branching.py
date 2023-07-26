from typing import List, Dict, Any, Optional

from flows.base_flows import CompositeFlow
from ..utils import logging
from flows.utils.general_helpers import validate_parameters

log = logging.get_logger(__name__)


class BranchingFlow(CompositeFlow):
    REQUIRED_KEYS_CONSTRUCTOR = ["subflows", "subflows_dict"]

    __default_flow_config = {
        "input_keys": ["branch", "branch_input_data"],
        "output_keys": ["branch_output_data"]
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @classmethod
    def _validate_parameters(cls, kwargs):
        validate_parameters(cls, kwargs)
        flow_config = kwargs["flow_config"]
        input_keys = flow_config["input_keys"]
        if input_keys != ["branch", "branch_input_data"]:
            raise ValueError(f"Branching flow is supposed to have fixed input_keys: ['branch', 'branch_input_data'], but current input_keys is {input_keys}")

        assert len(kwargs["subflows"]) > 0, f"Branching flow needs at least one flow, currently has 0"

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
            # print(f"Branching flow has subflows: {self.subflows}")
            raise ValueError(f"Branching flow has no subflow with name {branch}")
        # ~~~ Execute the flow and update state with answer ~~~
        output_message = self._call_flow_from_state(
            flow_to_call=current_flow
        )
       
        return {"branch_output_data": output_message.data["output_data"]}

    @classmethod
    def type(cls):
        return "branching"