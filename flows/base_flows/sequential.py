from typing import List, Dict, Any, Optional

from flows.base_flows import CircularFlow, Flow
from flows.data_transformations.abstract import DataTransformation
from ..utils import logging

log = logging.get_logger(__name__)

# ToDo(https://github.com/epfl-dlab/flows/issues/63): Add support for multiple runs (c.f. generator_critic.py)


class SequentialFlow(CircularFlow):

    __default_flow_config = {
        "max_rounds": 1,
    }

    def __init__(
            self,
            flow_config: Dict[str, Any],
            # input_data_transformations: List[DataTransformation],
            # output_data_transformations: List[DataTransformation],
            subflows: List[Flow],
    ):
        super().__init__(flow_config=flow_config,
                         # input_data_transformations=input_data_transformations,
                         # output_data_transformations=output_data_transformations,
                         subflows=subflows)

    @classmethod
    def type(cls):
        return "sequential"


