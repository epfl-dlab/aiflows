from typing import Dict, Any, List

from aiflows.data_transformations.abstract import DataTransformation
from aiflows.utils.general_helpers import flatten_dict, unflatten_dict
from aiflows.utils.logging import get_logger

log = get_logger(__name__)


class KeyDelete(DataTransformation):
    """This class deletes a list of keys from the data dictionary.

    :param keys_to_delete: A list of keys to delete
    :type keys_to_delete: List[str]
    :param flatten_data_dict: Whether to flatten the data dictionary before applying the transformation and unflatten it afterwards
    :type flatten_data_dict: bool, optional
    """

    def __init__(self, keys_to_delete: List[str], flatten_data_dict: bool = True):
        super().__init__()
        self.keys_to_delete = keys_to_delete
        self.flatten_data_dict = flatten_data_dict

    def __call__(self, data_dict: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        r"""Applies the transformation to the given data dictionary. It deletes a list of keys from the data dictionary.

        :param data_dict: The data dictionary to apply the transformation to
        :type data_dict: Dict[str, Any]
        :param \**kwargs: Arbitrary keyword arguments
        :return: The transformed data dictionary
        :rtype: Dict[str, Any]
        """

        if self.flatten_data_dict:
            data_dict = flatten_dict(data_dict)

        for key in self.keys_to_delete:
            data_dict.pop(key, None)

        if self.flatten_data_dict:
            data_dict = unflatten_dict(data_dict)

        return data_dict
