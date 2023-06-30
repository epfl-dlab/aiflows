from typing import Dict, Any

from flows.data_transformations.abstract import DataTransformation


class KeyRename(DataTransformation):
    def __init__(self,
                 old_key2new_key: Dict[str, str]):
        super().__init__()
        self.old_key2new_key = old_key2new_key

    def __call__(self, data_dict: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        # ToDo: Add support for nested keys (e.g. "a.b.c")
        for old_key, new_key in self.old_key2new_key.items():
            if old_key in data_dict:
                data_dict[new_key] = data_dict.pop(old_key)

        return data_dict
