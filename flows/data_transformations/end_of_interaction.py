from typing import Dict, Any

from .abstract import DataTransformation

from flows import utils

log = utils.get_pylogger(__name__)


class EndOfInteraction(DataTransformation):
    def __init__(self,
                 output_key: str,
                 end_of_interaction_string: str,
                 verbose: bool,
                 input_key: str = "raw_response"):
        super().__init__(output_key=output_key)
        self.input_key = input_key
        self.end_of_interaction_string = end_of_interaction_string
        self.verbose = verbose

    def __call__(self, data_dict: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        is_in = self.end_of_interaction_string.lower() in data_dict[self.input_key].lower()

        if self.verbose and is_in:
            log.info(f"End of interaction detected!")

        data_dict[self.output_key] = is_in
        return data_dict
