from typing import Dict, Any

from flows.data_transformations.abstract import DataTransformation
from flows.utils.general_helpers import flatten_dict, unflatten_dict
from flows.utils.logging import get_logger

log = get_logger(__name__)


class KeySelect(DataTransformation):
    def __init__(self,
                 keys_to_select: str,
                 flatten_data_dict: bool = True):
        super().__init__()
        self.flatten_data_dict = flatten_data_dict
        self.keys_to_select = keys_to_select

    def __call__(self, data_dict: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        if self.flatten_data_dict:
            data_dict = flatten_dict(data_dict)

        data_dict_to_return = {}
        for key in self.keys_to_select:
            data_dict_to_return[key] = data_dict[key]

        if self.flatten_data_dict:
            data_dict_to_return = unflatten_dict(data_dict_to_return)

        return data_dict_to_return
