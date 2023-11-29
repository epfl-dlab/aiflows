from abc import ABC
from typing import Dict, Any


class DataTransformation(ABC):
    """This class is the base class for all data transformations.

    :param output_key: The output key to apply the transformation to
    :type output_key: str, optional
    """

    def __init__(self, output_key=None):
        # if the output_key is set, the transformation will be applied only when the given output_key is requested
        self.output_key = output_key

    def __call__(self, data_dict: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        r"""Applies the transformation to the given data dictionary

        :param data_dict: The data dictionary to apply the transformation to
        :type data_dict: Dict[str, Any]
        :param \**kwargs: Arbitrary keyword arguments
        :return: The transformed data dictionary
        :rtype: Dict[str, Any]
        """
        raise NotImplementedError
