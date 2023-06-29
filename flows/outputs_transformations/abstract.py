from abc import ABC
from typing import Dict, Any


class OutputsTransformation(ABC):
    def __init__(self, **kwargs):
        self.params = kwargs

    def __call__(self, outputs: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        raise NotImplementedError
