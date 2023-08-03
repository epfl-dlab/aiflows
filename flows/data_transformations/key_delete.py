from typing import Dict, Any, List

from flows.data_transformations.abstract import DataTransformation
from flows.utils.general_helpers import flatten_dict, unflatten_dict
from flows.utils.logging import get_logger
log = get_logger(__name__)


class KeyDelete(DataTransformation):
    def __init__(self,
                 keys_to_delete: List[str],
                 flatten_data_dict: bool = True):
        super().__init__()
        self.keys_to_delete = keys_to_delete
        self.flatten_data_dict = flatten_data_dict

    def __call__(self, data_dict: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        if self.flatten_data_dict:
            data_dict = flatten_dict(data_dict)

        for key in self.keys_to_delete:
            data_dict.pop(key, None)

        if self.flatten_data_dict:
            data_dict = unflatten_dict(data_dict)

        return data_dict
