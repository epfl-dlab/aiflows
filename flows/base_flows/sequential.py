from typing import List, Dict, Any

from flows.base_flows import CircularFlow, Flow
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


