from typing import Dict, Any

from flows.data_transformations.abstract import DataTransformation


class KeyMatchInputInterface(DataTransformation):
    def __init__(self):
        super().__init__()

    def __call__(self, data_dict: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        dst_flow = kwargs["dst_flow"]

        input_keys = dst_flow.get_interface_description()["input"].keys()
        data_dict = {key: data_dict[key]
                     for key in input_keys}

        return data_dict
