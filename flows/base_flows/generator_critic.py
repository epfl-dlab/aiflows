from typing import List, Dict, Any, Optional

from flows.base_flows import CircularFlow
from ..utils import logging
from flows.utils.general_helpers import validate_parameters

log = logging.get_logger(__name__)

# ToDo(https://github.com/epfl-dlab/flows/issues/62): Add a flag controlling whether to skip the critic in the last round


class GeneratorCriticFlow(CircularFlow):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @classmethod
    def _validate_parameters(cls, kwargs):
        validate_parameters(cls, kwargs)

        for flow_name, flow in kwargs["subflows_dict"].items():
            if "generator" in flow_name.lower():
                continue
            elif "critic" in flow_name.lower():
                continue
            else:
                error_message = f"{cls.__class__.__name__} needs one flow with `critic` in its name" \
                                f"and one flow with `generator` in its name. Currently, the flow names are:" \
                                f"{kwargs['subflows'].keys()}"

                raise Exception(error_message)


    @classmethod
    def type(cls):
        return "GeneratorCriticFlow"
