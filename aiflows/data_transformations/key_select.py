from typing import Dict, Any, List

from aiflows.data_transformations.abstract import DataTransformation
from aiflows.utils.general_helpers import nested_keys_search, nested_keys_update
from aiflows.utils.logging import get_logger

log = get_logger(__name__)


class KeySelect(DataTransformation):
    """This class selects a list of keys from the data dictionary.

    :param keys_to_select: A list of keys to select
    :type keys_to_select: List[str]
    :param nested_keys: Whether to use nested keys
    :type nested_keys: bool, optional
    """

    def __init__(self, keys_to_select: List[str], nested_keys: bool = True):
        super().__init__()
        self.nested_keys = nested_keys
        self.keys_to_select = keys_to_select

    def __call__(self, data_dict: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        r"""Applies the transformation to the given data dictionary. It selects a list of keys from the data dictionary.

        :param data_dict: The data dictionary to apply the transformation to
        :type data_dict: Dict[str, Any]
        :param \**kwargs: Arbitrary keyword arguments
        :return: The transformed data dictionary
        :rtype: Dict[str, Any]
        """

        data_dict_to_return = {}
        if self.nested_keys:
            for key in self.keys_to_select:
                value, found = nested_keys_search(data_dict, key)
                if found:
                    nested_keys_update(data_dict_to_return, key, value)
                else:
                    raise KeyError(f"Key {key} not found in data_dict {data_dict}")
        else:
            for key in self.keys_to_select:
                data_dict_to_return[key] = data_dict[key]

        return data_dict_to_return
