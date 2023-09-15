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
    def type(cls):
        return "GeneratorCriticFlow"
