from typing import List, Dict, Any

from flows.base_flows import CircularFlow, Flow
from flows.utils.general_helpers import validate_flow_config
from ..utils import logging

log = logging.get_logger(__name__)


class SequentialFlow(CircularFlow):

    __default_flow_config = {
        "max_rounds": 1,
    }

    def __init__(
            self,
            flow_config: Dict[str, Any],
            subflows: List[Flow],
    ):
        super().__init__(flow_config=flow_config,
                         subflows=subflows)

    @classmethod
    def type(cls):
        return "sequential"

    def _on_reach_max_rounds(self):
        return

    @classmethod
    def _validate_flow_config(cls, kwargs):
        validate_flow_config(cls, kwargs)

        assert "max_rounds" in kwargs, "max_rounds must be specified in the config."
        assert kwargs["max_rounds"] == 1, "For a SequentialFlow, max_rounds must be 1."


