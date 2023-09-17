from typing import Dict, Any

from flows.data_transformations.abstract import DataTransformation
from flows.utils.general_helpers import nested_keys_search, nested_keys_update, nested_keys_pop
from flows.utils.logging import get_logger
log = get_logger(__name__)


class KeyRename(DataTransformation):
    def __init__(self,
                 old_key2new_key: Dict[str, str],
                 nested_keys: bool = True):
        super().__init__()
        self.old_key2new_key = old_key2new_key
        self.nested_keys = nested_keys

    def __call__(self, data_dict: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        if self.nested_keys:
            for old_key, new_key in self.old_key2new_key.items():
                value, found = nested_keys_search(data_dict, old_key)
                if found:
                    nested_keys_update(data_dict, new_key, value)
                    nested_keys_pop(data_dict, old_key)

        else:
            for old_key, new_key in self.old_key2new_key.items():
                if old_key in data_dict:
                    data_dict[new_key] = data_dict.pop(old_key) 

        return data_dict
