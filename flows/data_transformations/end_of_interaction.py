from typing import Dict, Any

from .abstract import DataTransformation

from ..utils import logging

log = logging.get_logger(__name__)


class EndOfInteraction(DataTransformation):
    """This class detects if the end of interaction string is in the input string.

    :param output_key: The output key to apply the transformation to
    :type output_key: str, optional
    :param end_of_interaction_string: The end of interaction string to detect
    :type end_of_interaction_string: str
    :param input_key: The input key to apply the transformation to
    :type input_key: str
    """

    def __init__(self, output_key: str, end_of_interaction_string: str, input_key: str):
        super().__init__(output_key=output_key)
        self.input_key = input_key
        self.end_of_interaction_string = end_of_interaction_string

    def __call__(self, data_dict: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        r"""Applies the transformation to the given data dictionary. It detects if the end of interaction string is in the input string.

        :param data_dict: The data dictionary to apply the transformation to
        :type data_dict: Dict[str, Any]
        :param \**kwargs: Arbitrary keyword arguments
        :return: The transformed data dictionary
        :rtype: Dict[str, Any]
        """

        # print(f"EndOfInteraction: {data_dict}, {self.end_of_interaction_string}")
        is_in = self.end_of_interaction_string.lower() in data_dict[self.input_key].lower()

        if is_in:
            log.info(f"End of interaction detected!")

        data_dict[self.output_key] = is_in
        return data_dict

    def __repr__(self) -> str:
        return f"EndOfInteraction(output_key={self.output_key}, end_of_interaction_string={self.end_of_interaction_string}, input_key={self.input_key})"
