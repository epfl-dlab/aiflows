from typing import List, Dict, Any, Optional

from flows.base_flows import CircularFlow
from flows.utils.general_helpers import validate_parameters
from ..utils import logging

log = logging.get_logger(__name__)

# ToDo(https://github.com/epfl-dlab/flows/issues/63): Add support for multiple runs (c.f. generator_critic.py)


class SequentialFlow(CircularFlow):
    REQUIRED_KEYS_CONFIG = [] # this is empty because SequentialFlow doesn't have any config and we need to overwrite the parent class
    REQUIRED_KEYS_CONSTRUCTOR = ["subflows"]

    def __init__(self, **kwargs):
        kwargs.setdefault("flow_config", {}).update({"max_rounds": 1})
        # set reset_every_round to False for all subflows but it should also work if it is set to be True
        # because the reset is only called once at the beginning of the run, where the flow doesn't have any state
        kwargs["flow_config"].update({"reset_every_round": {flow_name: False for flow_name in kwargs["subflows"].keys()}})
        super().__init__(**kwargs)


    @classmethod
    def type(cls):
        return "sequential"


