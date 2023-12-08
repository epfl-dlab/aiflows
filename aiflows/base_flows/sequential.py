from typing import List, Dict, Any

from aiflows.base_flows import CircularFlow, Flow
from aiflows.utils.general_helpers import validate_flow_config
from ..utils import logging

log = logging.get_logger(__name__)


class SequentialFlow(CircularFlow):
    """This class implements a sequential flow. It is a flow that consists of multiple sub-flows that are executed sequentially.
    It is a child class of CircularFlow. The only difference between a SequentialFlow and a CircularFlow is that the SequentialFlow has a max_rounds of 1.

    :param flow_config: The configuration of the flow. It must usually contain the following keys:
        - "subflows_config" (Dict[str,Any]): A dictionary of subflows configurations.The keys are the names of the subflows and the values are the configurations of the subflows.
        This is necessary when instantiating the flow from a config file.
        - The parameters required by the constructor of the parent class Flow
    :type flow_config: Dict[str, Any]
    :param subflows: A list of subflows. This is necessary when instantiating the flow programmatically.
    :type subflows: List[Flow]"""

    __default_flow_config = {
        "max_rounds": 1,
    }

    def __init__(
        self,
        flow_config: Dict[str, Any],
        subflows: List[Flow],
    ):
        super().__init__(flow_config=flow_config, subflows=subflows)

    @classmethod
    def type(cls):
        """Returns the type of the flow."""
        return "sequential"

    def _on_reach_max_rounds(self):
        """This method is called when the flow reaches the max_rounds (for a SequentialFlow, max_rounds is always 1).)"""
        return

    @classmethod
    def _validate_flow_config(cls, kwargs):
        """Validates the flow config. It raises an error if the flow config is invalid. (i.e. it's invalid if the max_rounds is not 1)"""
        validate_flow_config(cls, kwargs)

        assert "max_rounds" in kwargs, "max_rounds must be specified in the config."
        assert kwargs["max_rounds"] == 1, "For a SequentialFlow, max_rounds must be 1."
