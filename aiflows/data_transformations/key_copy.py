import copy
from typing import Dict, Any

from aiflows.data_transformations.abstract import DataTransformation
from aiflows.utils.general_helpers import flatten_dict, unflatten_dict


class KeyCopy(DataTransformation):
    """This class copies the value of a key to a new key. It can be used to rename a key.

    :param old_key2new_key: A dictionary mapping old keys to new keys
    :type old_key2new_key: Dict[str, str]
    :param flatten_data_dict: Whether to flatten the data dictionary before applying the transformation and unflatten it afterwards
    :type flatten_data_dict: bool, optional
    """

    def __init__(self, old_key2new_key: Dict[str, str], flatten_data_dict: bool = True):
        super().__init__()
        self.old_key2new_key = old_key2new_key
        self.flatten_data_dict = flatten_data_dict

    def __call__(self, data_dict: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        r"""Applies the transformation to the given data dictionary. It copies the value of a key to a new key. It can be used to rename a key.

        :param data_dict: The data dictionary to apply the transformation to
        :type data_dict: Dict[str, Any]
        :param \**kwargs: Arbitrary keyword arguments
        :return: The transformed data dictionary
        :rtype: Dict[str, Any]
        """
        if self.flatten_data_dict:
            data_dict = flatten_dict(data_dict)

        for old_key, new_key in self.old_key2new_key.items():
            if old_key in data_dict:
                data_dict[new_key] = copy.deepcopy(data_dict[old_key])

        if self.flatten_data_dict:
            data_dict = unflatten_dict(data_dict)

        return data_dict
