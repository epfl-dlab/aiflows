import os

import hydra

import flows
from flows.flow_launchers import FlowLauncher
from flows.flow_launchers.api_info import ApiInfo
from flows.utils.general_helpers import read_yaml_file

from flows import logging
from flows.flow_cache import CACHING_PARAMETERS, clear_cache

CACHING_PARAMETERS.do_caching = False  # Set to True in order to disable caching
# clear_cache() # Uncomment this line to clear the cache

logging.set_verbosity_debug()  # Uncomment this line to see verbose logs

from flows import flow_verse

dependencies = [
    {"url": "aiflows/OpenAIChatFlowModule", "revision": "6a1e351a915f00193f18f3da3b61c497df1d31a3"},
]
flow_verse.sync_dependencies(dependencies)

if __name__ == "__main__":
    # ~~~ Set the API information ~~~
    # OpenAI backend
    # api_information = ApiInfo("openai", os.getenv("OPENAI_API_KEY"))
    # Azure backend
    api_information = ApiInfo("azure", os.getenv("AZURE_OPENAI_KEY"), os.getenv("AZURE_OPENAI_ENDPOINT"))

    root_dir = "."
    cfg_path = os.path.join(root_dir, "simpleQA.yaml")
    cfg = read_yaml_file(cfg_path)

    # ~~~ Instantiate the Flow ~~~
    flow_with_interfaces = {
        "flow": hydra.utils.instantiate(cfg['flow'], _recursive_=False, _convert_="partial"),
        "input_interface": (
            None
            if getattr(cfg, "input_interface", None) is None
            else hydra.utils.instantiate(cfg['input_interface'], _recursive_=False)
        ),
        "output_interface": (
            None
            if getattr(cfg, "output_interface", None) is None
            else hydra.utils.instantiate(cfg['output_interface'], _recursive_=False)
        ),
    }

    # ~~~ Get the data ~~~
    data = {"id": 0, "question": "What is the capital of France?"}  # This can be a list of samples
    # data = {"id": 0, "question": "Who was the NBA champion in 2023?"}  # This can be a list of samples

    # ~~~ Run inference ~~~
    path_to_output_file = None
    # path_to_output_file = "output.jsonl"  # Uncomment this line to save the output to disk

    _, outputs = FlowLauncher.launch(
        flow_with_interfaces=flow_with_interfaces,
        data=data,
        path_to_output_file=path_to_output_file,
        api_information=api_information,
    )

    # ~~~ Print the output ~~~
    flow_output_data = outputs[0]
    print(flow_output_data)
