from abc import ABC
from typing import Dict, Any


class Interface(ABC):
    """This class is the base class for all interfaces."""

    def __init__(self):
        pass

    def __call__(self, data_dict: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        This method should be implemented by subclasses to perform a specific operation
        using the provided goal, source flow, destination flow, and data dictionary.

        :param goal: The goal of the operation.
        :param src_flow: The source flow of the operation.
        :param dst_flow: The destination flow of the operation.
        :param data_dict: A dictionary containing data needed for the operation.
        :param kwargs: Additional keyword arguments.
        :return: A dictionary containing the results of the operation.
        :raises NotImplementedError: This method must be implemented by a subclass.
        """
        raise NotImplementedError
