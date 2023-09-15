from typing import Dict, Any

import colorama

from .abstract import DataTransformation

from ..utils import logging

log = logging.get_logger(__name__)
colorama.init()


class PrintPreviousMessages(DataTransformation):
    def __init__(self, last_message_only=False):
        super().__init__()
        self.last_message_only = last_message_only

    def __call__(self, data_dict: Dict[str, Any], src_flow, **kwargs) -> Dict[str, Any]:
        previous_messages = src_flow.flow_state["previous_messages"]

        if self.last_message_only:
            previous_messages = [previous_messages[-1]]

        for msg in previous_messages:
            if msg.type == "system":
                color = colorama.Fore.YELLOW
            elif msg.type == "human":
                color = colorama.Fore.BLUE
            elif msg.type == "ai":
                color = colorama.Fore.RED

            message = f"\n{color} ~~~ [{src_flow.flow_config['name']}] Message (role: {msg.type}): \n" \
                      f"{colorama.Fore.WHITE}{msg.content}{colorama.Style.RESET_ALL}"
            log.info(message)

        return data_dict
    
    def __repr__(self) -> str:
        return f"PrintPreviousMessages"
