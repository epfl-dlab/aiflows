import os

import hydra

import flows
from flows.flow_launchers import FlowLauncher
from flows.utils.general_helpers import read_yaml_file

from flows import logging
from flows.flow_cache import CACHING_PARAMETERS, clear_cache

CACHING_PARAMETERS.do_caching = False  # Set to True in order to disable caching
# clear_cache() # Uncomment this line to clear the cache

logging.set_verbosity_debug()  # Uncomment this line to see verbose logs

# from flows import flow_verse (if the script requires a Flow from FlowVerse)
# dependencies = [
#     {"url": "martinjosifoski/OpenAIChatAtomicFlow", "revision": "main"},
# ]
# flow_verse.sync_dependencies(dependencies)

from flows.application_flows import OpenAIChatAtomicFlow
from flows.flow_launchers.api_info import ApiInfo


if __name__ == "__main__":
    # only specify needed api information here to avoid redundant information passing

    # to use openai backend, uncomment the following:
    # api_information = ApiInfo("openai", os.getenv("OPENAI_API_KEY"))
    # to use Azure as backend, uncomment the following:
    api_information = ApiInfo("azure", os.getenv("AZURE_OPENAI_KEY"), os.getenv("AZURE_OPENAI_ENDPOINT"))

    path_to_output_file = None
    # path_to_output_file = "output.jsonl"  # Uncomment this line to save the output to disk

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

    # ~~~ Run inference ~~~
    _, outputs = FlowLauncher.launch(
        flow_with_interfaces=flow_with_interfaces,
        data=data,
        path_to_output_file=path_to_output_file,
        api_information = api_information,
    )

    # ~~~ Print the output ~~~
    flow_output_data = outputs[0]
    print(flow_output_data)
