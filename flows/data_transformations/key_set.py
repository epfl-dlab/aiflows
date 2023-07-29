from typing import Dict, Any

from flows.data_transformations.abstract import DataTransformation
from flows.utils.general_helpers import flatten_dict, unflatten_dict
from flows.utils.logging import get_logger
log = get_logger(__name__)


class KeySet(DataTransformation):
    def __init__(self,
                 key: str,
                 value: Any,
                 flatten_data_dict: bool = False):
        super().__init__(key)
        self.flatten_data_dict = flatten_data_dict
        self.key = key
        self.value = value

    def __call__(self, data_dict: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        if self.flatten_data_dict:
            data_dict = flatten_dict(data_dict)

        if self.key in data_dict:
            log.warning(f'key: {self.key} already in data_dict, replacing value from {data_dict[self.key]} to {self.value}')
        data_dict[self.key] = self.value

        if self.flatten_data_dict:
            data_dict = unflatten_dict(data_dict)

        return data_dict
