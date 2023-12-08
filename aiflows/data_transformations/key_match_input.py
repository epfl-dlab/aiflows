from typing import Dict, Any

from aiflows.data_transformations.abstract import DataTransformation


class KeyMatchInput(DataTransformation):
    """This class extracts all keys from the data dictionary that are required by the destination flow."""

    def __init__(self):
        super().__init__()

    def __call__(self, data_dict: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        r"""Applies the transformation to the given data dictionary. It extracts all keys from the data dictionary that are required by the destination flow.

        :param data_dict: The data dictionary to apply the transformation to
        :type data_dict: Dict[str, Any]
        :param \**kwargs: Arbitrary keyword arguments
        :return: The transformed data dictionary
        :rtype: Dict[str, Any]
        """
        dst_flow = kwargs["dst_flow"]

        input_keys = dst_flow.get_interface_description()["input"]
        data_dict = {key: data_dict[key] for key in input_keys}

        return data_dict
