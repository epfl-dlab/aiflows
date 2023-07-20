import os

import hydra.utils

import flows
from flows import logging
from flows.utils import caching_utils
from flows.utils.caching_utils import clear_cache

caching_utils.CACHING_PARAMETERS.do_caching = True # Set to false to disable caching
# clear_cache() # Uncomment this line to clear the cache

from flows.flow_launchers import FlowLauncher

# logging.set_verbosity_debug()  # Uncomment this line to see verbose logs


# from flows import flow_verse
from flows.application_flows import HumanInputFlow
from flows.utils.general_helpers import read_yaml_file



if __name__ == "__main__":
    path_to_output_file = None
    # path_to_output_file = "output.jsonl"  # Uncomment this line to save the output to disk

    root_dir = "."
    cfg_path = os.path.join(root_dir, "HumanInput.yaml")
    overrides_config = read_yaml_file(cfg_path)

    # ~~~ Instantiate the flow ~~~
    # We can initialize the flow with hydra (we need to add the target in the yaml in that case)
    # flow = hydra.utils.instantiate(overrides_config, _convert_="partial", _recursive_=False)
    # or
    flow = HumanInputFlow.instantiate_from_default_config(overrides=overrides_config)

    # ~~~ Get the data ~~~
    data = {"id": 0, "question": "What is the capital of France?"}  # This can be a list of samples

    # ~~~ Run inference ~~~
    _, outputs = FlowLauncher.launch(
        flow=flow,
        data=data,
        path_to_output_file=path_to_output_file,
    )

    # ~~~ Print the output ~~~
    flow_output_data = outputs[0]
    print(flow_output_data)
