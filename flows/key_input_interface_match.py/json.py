import json
from typing import Dict, Any, Optional

from .abstract import DataTransformation

from ..utils import logging

log = logging.get_logger(__name__)


class Json2Obj(DataTransformation):
    def __init__(self,
                 input_key: str,
                 output_key: Optional[str] = None
                 ):
        super().__init__(output_key=output_key)
        self.input_key = input_key

    def __call__(self, data_dict: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        data_dict[self.output_key] = json.loads(data_dict[self.input_key])

        return data_dict


class Obj2Json(DataTransformation):
    def __init__(self,
                 input_key: str,
                 output_key: Optional[str] = None
                 ):
        super().__init__(output_key=output_key)
        self.input_key = input_key

    def __call__(self, data_dict: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        data_dict[self.output_key] = json.dumps(data_dict[self.input_key])

        return data_dict