from typing import Dict, Any

from .abstract import DataTransformation

from ..utils import logging

log = logging.get_logger(__name__)


class EndOfInteraction(DataTransformation):
    def __init__(self,
                 output_key: str,
                 end_of_interaction_string: str,
                 verbose: bool = False,
                 input_key: str = "raw_response"):
        super().__init__(output_key=output_key)
        self.input_key = input_key
        self.end_of_interaction_string = end_of_interaction_string

    def __call__(self, data_dict: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        is_in = self.end_of_interaction_string.lower() in data_dict[self.input_key].lower()

        if is_in:
            log.info(f"End of interaction detected!")

        data_dict[self.output_key] = is_in
        return data_dict
