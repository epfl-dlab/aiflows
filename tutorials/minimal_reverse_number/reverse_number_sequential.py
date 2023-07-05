import os
from typing import Dict, Optional, List, Any

from omegaconf import OmegaConf

from flows import logging
from flows.base_flows import SequentialFlow
from flows.flow_launchers import FlowLauncher
from flows.utils.general_helpers import read_yaml_file


# logging.set_verbosity_debug()  # Uncomment this line to see verbose logs


if __name__ == "__main__":
    path_to_output_file = None
    # path_to_output_file = "output.jsonl"  # ToDo: Uncomment this line to save the output to a file

    root_dir = "."
    cfg_path = os.path.join(root_dir, "reverseNumberSequential.yaml")
    overrides_config = read_yaml_file(cfg_path)

    # ~~~ Instantiate the flow ~~~
    flow = SequentialFlow.instantiate_from_default_config(overrides=overrides_config)

    # ~~~ Get the data ~~~
    data = {"id": 0, "number": 1234}  # This can be a list of samples

    # ~~~ Run inference ~~~
    outputs = FlowLauncher.launch(
        flow=flow,
        data=data,
        path_to_output_file=path_to_output_file,
    )

    # ~~~ Print the output ~~~
    first_inference_output_for_sample = outputs[0]["inference_outputs"][0]
    output_message_data = first_inference_output_for_sample.data
    flow_output_data = output_message_data["output_data"]
    print(flow_output_data)
