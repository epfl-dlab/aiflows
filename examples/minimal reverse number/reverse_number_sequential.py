import os

import aiflows
from aiflows.flow_launchers import FlowLauncher
from aiflows.base_flows import SequentialFlow

from aiflows.utils.general_helpers import read_yaml_file


# logging.set_verbosity_debug()  # Uncomment this line to see verbose logs


if __name__ == "__main__":
    root_dir = "."
    cfg_path = os.path.join(root_dir, "reverseNumberSequential.yaml")
    cfg = read_yaml_file(cfg_path)

    # ~~~ Instantiate the flow ~~~
    flow = SequentialFlow.instantiate_from_default_config(**cfg)

    # ~~~ Get the data ~~~
    data = {"id": 0, "number": 1234}  # This can be a list of samples

    # ~~~ Run inference ~~~
    path_to_output_file = None
    # path_to_output_file = "output.jsonl"
    _, outputs = FlowLauncher.launch(
        flow_with_interfaces={"flow": flow}, data=data, path_to_output_file=path_to_output_file
    )

    # ~~~ Print the output ~~~
    flow_output_data = outputs[0]
    print(flow_output_data)
