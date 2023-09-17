from typing import List, Dict, Any, Optional, Tuple

from flows.base_flows import CompositeFlow, Flow
from ..utils import logging
from flows.utils.general_helpers import validate_parameters
from flows.interfaces.key_interface import KeyInterface
from flows.data_transformations import KeyMatchInput

log = logging.get_logger(__name__)

class BranchingFlow(CompositeFlow):

    __default_flow_config = {
        "input_interface": ["branch", "branch_input_data"],
        "output_interface": ["branch_output_data"]
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        branch = input_data["branch"]
        branch_input_data = input_data["branch_input_data"]

        branch_flow = self._get_subflow(branch)
        if branch_flow is None:
            raise ValueError(f"Branching flow has no subflow with name {branch}")
        
        api_keys = self._get_from_state("api_keys")
        input_message = self._package_input_message(
            payload=branch_input_data,
            dst_flow=branch_flow,
            api_keys=api_keys
        )

        output_message = branch_flow(input_message)

        self._log_message(output_message)

        return {"branch_output_data": output_message.data["output_data"]}

    @classmethod
    def type(cls):
        return "branching"