from typing import Dict, Any

from flows.data_transformations.abstract import DataTransformation
from flows.utils.general_helpers import flatten_dict, unflatten_dict
from flows.utils.logging import get_logger
log = get_logger(__name__)


class KeySet(DataTransformation):
    def __init__(self,
                 key2value: Dict[str, str],
                 flatten_data_dict: bool = True):
        super().__init__()
        self.flatten_data_dict = flatten_data_dict
        self.key2value = key2value

    def __call__(self, data_dict: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        if self.flatten_data_dict:
            data_dict = flatten_dict(data_dict)

        for key, value in self.key2value.items():
            data_dict[key] = value

        if self.flatten_data_dict:
            data_dict = unflatten_dict(data_dict)

        return data_dict
