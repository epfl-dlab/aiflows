import copy
from abc import ABC
from typing import Dict, Any, List,Union
from aiflows.messages import FlowMessage

import hydra

from aiflows.data_transformations import KeySelect, KeyRename, KeyCopy, KeySet, KeyDelete


class KeyInterface(ABC):
    """This class is the base class for all key interfaces. It applies a list of transformations to a data dictionary.

    :param keys_to_rename: A dictionary mapping old keys to new keys (used to instantiate the transformation defined in the KeyRename class)
    :type keys_to_rename: Dict[str, str], optional
    :param keys_to_copy: A dictionary mapping old keys to new keys (used to instantiate the transformation defined in the KeyCopy class)
    :type keys_to_copy: Dict[str, str], optional
    :param keys_to_set: A dictionary mapping keys to values (used to instantiate the transformation defined in the KeySet class)
    :type keys_to_set: Dict[str, str], optional
    :param additional_transformations: A list of additional transformations to apply to the data dictionary
    :type additional_transformations: List, optional
    :param keys_to_select: A list of keys to select (used to instantiate the transformation defined in the KeySelect class)
    :type keys_to_select: List[str], optional
    :param keys_to_delete: A list of keys to delete (used to instantiate the transformation defined in the KeyDelete class)
    :type keys_to_delete: List[str], optional
    """

    @staticmethod
    def _set_up_transformations(transformations: List):
        """Static method that instantiates a list of transformations with the hydra framework.

        :param transformations: A list of transformations to instantiate
        :type transformations: List
        :return: A list of instantiated transformations
        :rtype: List
        """
        transforms = []
        if len(transformations) > 0:
            for transf in transformations:
                #Not very pretty but this would fail if the transformation is not a hydra config and if
                #we except than I'm assuming it's a callable (function or class..)
                try:
                    transforms.append(hydra.utils.instantiate(transf, _convert_="partial"))
                except:
                    transforms.append(transf)
        return transforms

    def __init__(
        self,
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

    def __call__(self, data: Union[FlowMessage, Dict[str,Any]], **kwargs) -> Union[FlowMessage, Dict[str,Any]]:
        r"""Applies the all transformations to the given data dictionary.

        :param goal: The goal of the flow
        :type goal: str
        :param src_flow: The source flow
        :type src_flow: str
        :param dst_flow: The destination flow
        :type dst_flow: str
        :param data: The data dictionary or message to apply the transformations to
        :type data: Union[FlowMessage, Dict[str,Any]]
        :param \**kwargs: Arbitrary keyword arguments (arguments that are passed to the transformations)
        :return: The transformed data dictionary or message
        :rtype:  Union[FlowMessage, Dict[str,Any]
        """
        
        if isinstance(data, FlowMessage):
            data_dict = data.data
        else:
            data_dict = data
        
        data_dict = copy.deepcopy(data_dict)
        # print(f"src_flow: {src_flow.name}, dst_flow: {dst_flow.name}")
        for transformation in self.transformations:
            # print(f"before transformation: {transformation}, data_dict: {data_dict}")
            data_dict = transformation(data_dict=data_dict, **kwargs)
            # print(f"after transformation: {transformation}, data_dict: {data_dict}")

        if isinstance(data, FlowMessage):
            data.data = data_dict
            return data
        
        return data_dict
        

