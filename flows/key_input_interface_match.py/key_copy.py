import copy
from typing import Dict, Any

from flows.data_transformations.abstract import DataTransformation
from flows.utils.general_helpers import flatten_dict, unflatten_dict


class KeyCopy(DataTransformation):
    def __init__(self,
                 old_key2new_key: Dict[str, str],
                 flatten_data_dict: bool = True):
        super().__init__()
        self.old_key2new_key = old_key2new_key
        self.flatten_data_dict = flatten_data_dict

    def __call__(self, data_dict: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        if self.flatten_data_dict:
            data_dict = flatten_dict(data_dict)

        for old_key, new_key in self.old_key2new_key.items():
            if old_key in data_dict:
                data_dict[new_key] = copy.deepcopy(data_dict[old_key])

        if self.flatten_data_dict:
            data_dict = unflatten_dict(data_dict)

        return data_dict
