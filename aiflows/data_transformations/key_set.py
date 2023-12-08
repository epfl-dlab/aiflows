from typing import Dict, Any

from aiflows.data_transformations.abstract import DataTransformation
from aiflows.utils.general_helpers import flatten_dict, unflatten_dict
from aiflows.utils.logging import get_logger

log = get_logger(__name__)


class KeySet(DataTransformation):
    """This class sets a list of keys to a given value in the data dictionary.

    :param key2value: A dictionary mapping keys to values
    :type key2value: Dict[str, str]
    :param flatten_data_dict: Whether to flatten the data dictionary before applying the transformation and unflatten it afterwards
    :type flatten_data_dict: bool, optional
    """

    def __init__(self, key2value: Dict[str, str], flatten_data_dict: bool = True):
        super().__init__()
        self.flatten_data_dict = flatten_data_dict
        self.key2value = key2value

    def __call__(self, data_dict: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        r"""Applies the transformation to the given data dictionary. It sets a list of keys to a given value in the data dictionary.

        :param data_dict: The data dictionary to apply the transformation to
        :type data_dict: Dict[str, Any]
        :param \**kwargs: Arbitrary keyword arguments
        :return: The transformed data dictionary
        :rtype: Dict[str, Any]
        """
        if self.flatten_data_dict:
            data_dict = flatten_dict(data_dict)

        for key, value in self.key2value.items():
            data_dict[key] = value

        if self.flatten_data_dict:
            data_dict = unflatten_dict(data_dict)

        return data_dict
