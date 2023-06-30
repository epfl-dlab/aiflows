from abc import ABC
from typing import Dict, Any


class DataTransformation(ABC):
    def __init__(self, output_key=None):
        # if the output_key is set, the transformation will be applied only when the given output_key is requested
        self.output_key = output_key

    def __call__(self, data_dict: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        raise NotImplementedError
