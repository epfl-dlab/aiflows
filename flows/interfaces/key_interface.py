import copy
from abc import ABC
from typing import Dict, Any, List

import hydra

from flows.data_transformations import KeySelect, KeyRename, KeyCopy, KeySet, KeyDelete


class KeyInterface(ABC):
    @staticmethod
    def _set_up_transformations(transformations: List):
        transforms = []
        if len(transformations) > 0:
            for config in transformations:
                transforms.append(hydra.utils.instantiate(config, _convert_="partial"))

        return transforms

    def __init__(self,
                 keys_to_rename: Dict[str, str] = {},
                 keys_to_copy: Dict[str, str] = {},
                 keys_to_set: Dict[str, Any] = {},
                 additional_transformations: List = [],
                 keys_to_select: List[str] = [],
                 keys_to_delete: List[str] = [],
                 ):
        self.transformations = []

        if keys_to_rename:
            self.transformations.append(KeyRename(keys_to_rename))
        if keys_to_copy:
            self.transformations.append(KeyCopy(keys_to_copy))
        if keys_to_set:
            self.transformations.append(KeySet(keys_to_set))

        additional_transforms = self._set_up_transformations(additional_transformations)
        self.transformations.extend(additional_transforms)

        if keys_to_select:
            self.transformations.append(KeySelect(keys_to_select))
        if keys_to_delete:
            self.transformations.append(KeyDelete(keys_to_delete))

    def __call__(self, goal, src_flow, dst_flow, data_dict: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        data_dict = copy.deepcopy(data_dict)
        kwargs["goal"] = goal
        kwargs["src_flow"] = src_flow
        kwargs["dst_flow"] = dst_flow
        # print(f"src_flow: {src_flow.name}, dst_flow: {dst_flow.name}")
        for transformation in self.transformations:
            # print(f"before transformation: {transformation}, data_dict: {data_dict}")
            data_dict = transformation(data_dict=data_dict, **kwargs)
            # print(f"after transformation: {transformation}, data_dict: {data_dict}")

        return data_dict
