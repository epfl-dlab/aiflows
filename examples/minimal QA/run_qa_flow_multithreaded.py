import os

import hydra.utils

from flows import logging
from flows.datasets import OutputsDataset
from flows.flow_cache import CACHING_PARAMETERS, clear_cache
from flows.flow_launchers import FlowMultiThreadedAPILauncher

CACHING_PARAMETERS.do_caching = False  # Set to True in order to disable caching
# clear_cache() # Uncomment this line to clear the cache

logging.set_verbosity_debug()  # Uncomment this line to see verbose logs

from flows.utils.general_helpers import read_yaml_file
from flows.backends.api_info import ApiInfo

from flows import flow_verse
dependencies = [
    {"url": "aiflows/OpenAIChatFlowModule", "revision": "6a1e351a915f00193f18f3da3b61c497df1d31a3"},
]
flow_verse.sync_dependencies(dependencies)

if __name__ == "__main__":
    root_dir = "examples/minimal QA"

    openai_api = ApiInfo(backend_used="openai", api_key = os.getenv("OPENAI_API_KEY"))
    # # Azure backend
    azure_api = ApiInfo(backend_used = "azure",
                              api_base = os.getenv("AZURE_API_BASE"),
                              api_key = os.getenv("AZURE_OPENAI_KEY"),
                              api_version =  os.getenv("AZURE_API_VERSION") )
    
    # ~~~ Launcher Configuration ~~~
    output_dir = "predictions"
    api_information = [openai_api,azure_api]

    launcher_config = {
        "n_api_keys": len(api_information),
        "single_threaded": False,
        "fault_tolerant_mode": False,
        "n_batch_retries": 2,
        "wait_time_between_retries": 6,
        "n_workers_per_key": 2,
        "debug": False,
        "n_independent_samples": 1,
        "output_keys": None
    }

    # ~~~ Instantiate the Flows ~~~
    cfg_path = os.path.join(root_dir, "simpleQA.yaml")
    cfg = read_yaml_file(cfg_path)
    
    cfg["flow"]["backend"]["api_infos"] = api_information
    
    if launcher_config["single_threaded"]:
        n_workers = 1
    else:
        n_workers = launcher_config["n_workers_per_key"] * len(api_information)

    flow_instances = []
    for _ in range(n_workers):
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
        flow_instances.append(flow_with_interfaces)

    # ~~~ Get the data ~~~
    data = [{"id": 0, "question": "What is the capital of France?"},
            {"id": 1, "question": "What is the capital of Germany?"},
            {"id": 2, "question": "What is the capital of Switzerland?"},
            {"id": 3, "question": "What is the capital of The United States?"}]

    # ~~~ Run inference ~~~
    launcher = FlowMultiThreadedAPILauncher(**launcher_config)
    launcher.predict_dataloader(data, flows_with_interfaces=flow_instances)

    # ~~~ Print the output ~~~
    output_dataset = OutputsDataset(data_dir=output_dir)
    for output in output_dataset:
        print("~~~", "ID: ", output["id"], "~~~")
        print(output_dataset.get_output_data(output, idx=0))
