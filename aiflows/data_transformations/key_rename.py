from typing import Dict, Any

from aiflows.data_transformations.abstract import DataTransformation
from aiflows.utils.general_helpers import nested_keys_search, nested_keys_update, nested_keys_pop
from aiflows.utils.logging import get_logger

log = get_logger(__name__)


class KeyRename(DataTransformation):
    """This class renames a list of keys from the data dictionary.

    :param old_key2new_key: A dictionary mapping old keys to new keys
    :type old_key2new_key: Dict[str, str]
    :param nested_keys: Whether to use nested keys
    :type nested_keys: bool, optional
    """

    def __init__(self, old_key2new_key: Dict[str, str], nested_keys: bool = True):
        super().__init__()
        self.old_key2new_key = old_key2new_key
        self.nested_keys = nested_keys

    def __call__(self, data_dict: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        r"""
        Applies the transformation to the given data dictionary. It renames a list of keys from the data dictionary.

        :param data_dict: The data dictionary to apply the transformation to
        :type data_dict: Dict[str, Any]
        :param \**kwargs: Arbitrary keyword arguments
        :return: The transformed data dictionary
        :rtype: Dict[str, Any]
        """
        if self.nested_keys:
            for old_key, new_key in self.old_key2new_key.items():
                # Had to add because it was failing for cases where old_key == new_key (was poping key it just had updated)
                if old_key != new_key: 
                    value, found = nested_keys_search(data_dict, old_key)
                    if found:
                        nested_keys_update(data_dict, new_key, value)
                        nested_keys_pop(data_dict, old_key)

        else:
            for old_key, new_key in self.old_key2new_key.items():
                if old_key in data_dict:
                    data_dict[new_key] = data_dict.pop(old_key)

        return data_dict
