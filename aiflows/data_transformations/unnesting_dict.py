from typing import Dict, Any, Optional

from aiflows.data_transformations.abstract import DataTransformation
from aiflows.utils.general_helpers import flatten_dict, unflatten_dict
from aiflows.utils.logging import get_logger

log = get_logger(__name__)


class UnNesting(DataTransformation):
    """This class unnests a dictionary from the data dictionary.

    :param input_key: The key of the dictionary to unnest
    :type input_key: str
    :param output_key: The output key to save the transformed data to
    :type output_key: str, optional
    """

    def __init__(self, input_key: str, output_key: Optional[str] = None):
        super().__init__(output_key=output_key)
        self.input_key = input_key

    def __call__(self, data_dict: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Applies the transformation to the given data dictionary. It unnests a dictionary from the data dictionary.

        :param data_dict: The data dictionary to apply the transformation to
        :type data_dict: Dict[str, Any]
        :return: The transformed data dictionary
        :rtype: Dict[str, Any]
        """
        if self.input_key not in data_dict:
            raise ValueError(f"input_key: {self.input_key} not in data_dict, available keys: {data_dict.keys()}")
        else:
            unnested_data_dict = data_dict[self.input_key]
            del data_dict[self.input_key]
            data_dict.update(unnested_data_dict)

        return data_dict
