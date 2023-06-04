from abc import ABC
from typing import Dict, Any


class MessageAnnotator(ABC):
    key: str

    def __init__(self, **kwargs):
        self.params = kwargs

    def __call__(self, message: str, **kwargs) -> Dict[str, Any]:
        raise NotImplementedError
