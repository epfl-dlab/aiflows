from abc import ABC
from typing import Dict, Any, List

from flows.data_transformations import KeySelect, KeyRename, KeyCopy, KeySet, KeyDelete


class KeyInterface(ABC):
    def __init__(self,
                 keys_to_select: List[str] = [],
                 keys_to_rename: Dict[str, str] = {},
                 keys_to_copy: Dict[str, str] = {},
                 keys_to_set: Dict[str, Any] = {},
                 keys_to_delete: List[str] = [],
                 additional_transformations: List = [],
                 ):
        self.transformations = []

        if keys_to_select:
            self.transformations.append(KeySelect(keys_to_select))
        if keys_to_rename:
            self.transformations.append(KeyRename(keys_to_rename))
        if keys_to_copy:
            self.transformations.append(KeyCopy(keys_to_copy))
        if keys_to_set:
            self.transformations.append(KeySet(keys_to_set))
        if keys_to_delete:
            self.transformations.append(KeyDelete(keys_to_delete))

        self.transformations.extend(additional_transformations)  # Add code parsing to the CodeFlow

    def __call__(self, goal, src_flow, dst_flow, data_dict: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        kwargs["goal"] = goal
        kwargs["src_flow"] = src_flow
        kwargs["dst_flow"] = dst_flow

        for transformation in self.transformations:
            data_dict = transformation(data_dict=data_dict, **kwargs)

        return data_dict
