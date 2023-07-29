from typing import Dict, Any, Optional

from flows.data_transformations.abstract import DataTransformation
from flows.utils.general_helpers import flatten_dict, unflatten_dict
from flows.utils.logging import get_logger

log = get_logger(__name__)


class UnNesting(DataTransformation):
    def __init__(self,
                 input_key: str,
                 output_key: Optional[str] = None):
        super().__init__(output_key=output_key)
        self.input_key = input_key

    def __call__(self, data_dict: Dict[str, Any], **kwargs) -> Dict[str, Any]:

        if self.input_key not  in data_dict:
            raise ValueError(f'input_key: {self.input_key} not in data_dict, available keys: {data_dict.keys()}')
        else:
            unnested_data_dict = data_dict[self.input_key]
            del data_dict[self.input_key]
            data_dict.update(unnested_data_dict)

        return data_dict
