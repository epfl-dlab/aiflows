from typing import Dict, Any

from flows.base_flows import CompositeFlow
from ..utils import logging

log = logging.get_logger(__name__)

# draw a diagram of what the branching flow would look like
class BranchingFlow(CompositeFlow):
    """This class implements a branching flow. A branching flow is a composite flow that has multiple subflows. The subflow to be executed is determined by the value of the "branch" key in the input data dictionary passed to the flow.
    Example in an Illustration:
            input                                   BranchingFlow                         output
            -----                                   -------------                         ------

                                                    |---–> subflow_1
                                                |---|--–-> subflow_2 ------|
    input_data["branch"] = "subflow_2"  --------|   |----> subflow_3       |-> output_data = subflow_2(input_data)
                                                    |----> ....
                                                    |---–> subflow_n

    :param \**kwargs: The keyword arguments passed to the CompositeFlow constructor

    """

    __default_flow_config = {
        "input_interface": ["branch", "branch_input_data"],
        "output_interface": ["branch_output_data"],
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Runs the branching flow. The subflow to be executed is determined by the value of the "branch" key in the input data dictionary passed to the flow.

        :param input_data: The input data dictionary
        :type input_data: Dict[str, Any]
        :return: The output data dictionary
        :rtype: Dict[str, Any]
        """
        branch = input_data["branch"]
        branch_input_data = input_data["branch_input_data"]

        branch_flow = self._get_subflow(branch)
        if branch_flow is None:
            raise ValueError(f"Branching flow has no subflow with name {branch}")

        input_message = self._package_input_message(payload=branch_input_data, dst_flow=branch_flow)

        output_message = branch_flow(input_message)

        self._log_message(output_message)

        return {"branch_output_data": output_message.data["output_data"]}

    @classmethod
    def type(cls):
        """Returns the type of the flow as a string."""
        return "branching"
