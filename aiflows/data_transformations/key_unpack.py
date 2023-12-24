from typing import Dict, Any, List

from aiflows.data_transformations.abstract import DataTransformation
from aiflows.utils.logging import get_logger
from aiflows.utils.general_helpers import nested_keys_search

log = get_logger(__name__)


class KeyUnpack(DataTransformation):
    """This class unpacks one layer of the nested data dictionary.
    :param keys_to_unpack: A list of keys to unpack
    :type keys_to_unpack: List[str]
    :return The unpacked data dictionary

    example:
    keys_to_unpack: ["observation"]
    data_dict = {
    "observation":
        "code": "some code",
        "file_loc": "some path",
        "human_feedback": "some feedback"
    }
    output = {
    "code": "some code",
    "file_loc": "some path",
    "human_feedback":"some feedback"
    }
    """

    def __init__(self,
                 keys_to_unpack: List[str],
                 nested_keys: bool = True
                 ):
        super().__init__()
        self.keys_to_unpack = keys_to_unpack
        self.nested_keys = nested_keys

    def __call__(self, data_dict: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        ret = data_dict.copy()
        if self.nested_keys:
            for key_to_unpack in self.keys_to_unpack:
                nested_keys = key_to_unpack.split(".")
                value, found = nested_keys_search(ret, key_to_unpack)
                if found and len(nested_keys) > 1:
                    parent_key = nested_keys[0]
                    ret[parent_key] = value
                elif found and len(nested_keys) == 1:
                    ret = value
        else:
            for key_to_unpack in self.keys_to_unpack:
                ret = ret.get(key_to_unpack, ret)
        return ret
