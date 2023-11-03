import os

import hydra

import flows
from flows.flow_launchers import FlowLauncher, ApiInfo
from flows.utils.general_helpers import read_yaml_file

from flows import logging
from flows.flow_cache import CACHING_PARAMETERS, clear_cache

CACHING_PARAMETERS.do_caching = False  # Set to True in order to disable caching
# clear_cache() # Uncomment this line to clear the cache

logging.set_verbosity_debug()

dependencies = [
    {"url": "aiflows/LCToolFlowModule", "revision": "46dd24ecc3dc4f4f0191e57c202cc7d20e8e7782"},
    {"url": "aiflows/ControllerExecutorFlowModule", "revision": "ba2c90bb9b0539af39ccad90c98a2ba1f9a22c91"},
]
from flows import flow_verse

flow_verse.sync_dependencies(dependencies)

if __name__ == "__main__":
    # ~~~ Set the API information ~~~
    # OpenAI backend
    # api_information = ApiInfo("openai", os.getenv("OPENAI_API_KEY"))
    # Azure backend
    api_information = ApiInfo("azure", os.getenv("AZURE_OPENAI_KEY"), os.getenv("AZURE_OPENAI_ENDPOINT"))

    path_to_output_file = None
    # path_to_output_file = "output.jsonl"  # Uncomment this line to save the output to disk

    root_dir = "."
    cfg_path = os.path.join(root_dir, "ReAct.yaml")
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
    # This can be a list of samples
    # data = {"id": 0, "goal": "Answer the following question: What is the population of Canada?"}  # Uses wikipedia
    data = {"id": 0, "goal": "Answer the following question: Who was the NBA champion in 2023?"}

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
