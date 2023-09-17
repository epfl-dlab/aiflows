from typing import Dict, Any, List

from flows.data_transformations.abstract import DataTransformation
from flows.utils.general_helpers import nested_keys_search, nested_keys_update
from flows.utils.logging import get_logger

log = get_logger(__name__)


class KeySelect(DataTransformation):
    def __init__(self,
                 keys_to_select: List[str],
                 nested_keys: bool = True):
        super().__init__()
        self.nested_keys = nested_keys
        self.keys_to_select = keys_to_select

    def __call__(self, data_dict: Dict[str, Any], **kwargs) -> Dict[str, Any]:
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
