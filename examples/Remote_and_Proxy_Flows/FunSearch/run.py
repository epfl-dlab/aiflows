"""A simple script to run a Flow that can be used for development and debugging."""

import os

import hydra

import aiflows
from aiflows.flow_launchers import FlowLauncher
from aiflows.utils.general_helpers import read_yaml_file

from aiflows import logging
from aiflows.flow_cache import CACHING_PARAMETERS, clear_cache
from aiflows.backends.api_info import ApiInfo
CACHING_PARAMETERS.do_caching = False  # Set to True to enable caching
# clear_cache() # Uncomment this line to clear the cache

logging.set_verbosity_debug()

dependencies = [
    {"url": "aiflows/EvaluatorFlowModule", "revision": "FlowVerse/EvaluatorFlowModule"},
    {"url": "aiflows/ProgramDBFlowModule", "revision": "FlowVerse/ProgramDBFlowModule"},
    {"url": "aiflows/SamplerFlowModule", "revision": "FlowVerse/SamplerFlowModule"},
]

from aiflows import flow_verse
flow_verse.sync_dependencies(dependencies)
from flow_modules.aiflows.ProgramDBFlowModule.Loader import Loader

if __name__ == "__main__":
    
    api_information = ApiInfo(backend_used="openai", api_key=os.getenv("OPENAI_API_KEY"))
    # ~~~ Instantiate the Flow ~~~
    root_dir = "."
    cfg_path = os.path.join(root_dir, "demo.yaml")
    cfg = read_yaml_file(cfg_path)
    cfg["flow"]["subflows_config"]["SamplerFlow"]["backend"]["api_infos"] = api_information
    # ~~~ Instantiate the Flow ~~~
    flow_with_interfaces = {
        "flow": hydra.utils.instantiate(cfg['flow'], _recursive_=False, _convert_="partial"),
        "input_interface": (
            None
            if cfg.get( "input_interface", None) is None
            else hydra.utils.instantiate(cfg['input_interface'], _recursive_=False)
        ),
        "output_interface": (
            None
            if cfg.get( "output_interface", None) is None
            else hydra.utils.instantiate(cfg['output_interface'], _recursive_=False)
        ),
    }
    # ~~~ Get the data ~~~
    # This can be a list of samples
    artifact_file_path ="functions.py"
    artifact_to_evolve_name = "priority_function"
    artifact_to_evolve: str= Loader(file_path = artifact_file_path,target_name = artifact_to_evolve_name).load_target()
    data = {"id": 0,"artifact": artifact_to_evolve}  # Add your data here
       
    # ~~~ Run inference ~~~
    path_to_output_file = None
    # path_to_output_file = "output.jsonl"  # Uncomment this line to save the output to disk

    _, outputs = FlowLauncher.launch(
        flow_with_interfaces=flow_with_interfaces,
        data=data,
        path_to_output_file=path_to_output_file,
    )

    # ~~~ Print the output ~~~
    flow_output_data = outputs[0]
    print(flow_output_data[0]["artifact"])
