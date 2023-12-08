import json
from typing import Dict, Any, Optional

from .abstract import DataTransformation

from aiflows.utils import logging

log = logging.get_logger(__name__)


class Json2Obj(DataTransformation):
    """This class converts a JSON string to a Python object.

    :param input_key: The input key to apply the transformation to
    :type input_key: str
    :param output_key: The output key to save the transformed data to
    :type output_key: str, optional
    """

    def __init__(self, input_key: str, output_key: Optional[str] = None):
        super().__init__(output_key=output_key)
        self.input_key = input_key

    def __call__(self, data_dict: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Applies the transformation to the given data dictionary. It converts a JSON string to a Python object.

        :param data_dict: The data dictionary to apply the transformation to
        :type data_dict: Dict[str, Any]
        :return: The transformed data dictionary
        :rtype: Dict[str, Any]
        """
        data_dict[self.output_key] = json.loads(data_dict[self.input_key])

        return data_dict


class Obj2Json(DataTransformation):
    """This class converts a Python object to a JSON string.

    :param input_key: The input key to apply the transformation to
    :type input_key: str
    :param output_key: The output key to save the transformed data to
    :type output_key: str, optional

    """

    def __init__(self, input_key: str, output_key: Optional[str] = None):
        super().__init__(output_key=output_key)
        self.input_key = input_key

    def __call__(self, data_dict: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        r"""Applies the transformation to the given data dictionary. It converts a Python object to a JSON string.

        :param data_dict: The data dictionary to apply the transformation to
        :type data_dict: Dict[str, Any]
        :param \**kwargs: Arbitrary keyword arguments
        :return: The transformed data dictionary
        :rtype: Dict[str, Any]
        """

        data_dict[self.output_key] = json.dumps(data_dict[self.input_key])

        return data_dict
