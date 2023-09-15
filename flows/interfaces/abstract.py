from abc import ABC
from typing import Dict, Any


class Interface(ABC):
    def __init__(self):
        pass

    def __call__(self, goal, src_flow, dst_flow, data_dict: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        raise NotImplementedError
