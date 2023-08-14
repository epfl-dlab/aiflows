from flows.base_flows import CircularFlow
from flows.utils import logging

log = logging.get_logger(__name__)


class OpenAIChatHumanFlowModule(CircularFlow):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @classmethod
    def type(cls):
        return "OpenAIChatHumanFlowModule"
