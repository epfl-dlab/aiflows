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

# from flows import flow_verse (if the script requires a Flow from FlowVerse)
# dependencies = [
#     {"url": "martinjosifoski/OpenAIChatAtomicFlow", "revision": "main"},
# ]
# flow_verse.sync_dependencies(dependencies)

from flows.application_flows import OpenAIChatAtomicFlow


if __name__ == "__main__":
    root_dir = "."

    # ~~~ Launcher Configuration ~~~
    output_dir = "predictions"
    api_keys = {"openai": os.getenv("OPENAI_API_KEY")}
    api_keys["azure"] = os.getenv("AZURE_OPENAI_KEY")
    endpoints = {"azure": os.getenv("AZURE_OPENAI_ENDPOINT")}

    launcher_config = {
        "api_keys": api_keys,
        "endpoints": endpoints,
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

    if launcher_config["single_threaded"]:
        n_workers = 1
    else:
        n_workers = launcher_config["n_workers_per_key"] * len(api_keys)

    flow_instances = []
    # for _ in range(n_workers):
    #     flow_with_interfaces = {
    #         "flow": hydra.utils.instantiate(cfg['flow'], _recursive_=False, _convert_="partial"),
    #         "input_interface": (
    #             None
    #             if getattr(cfg, "input_interface", None) is None
    #             else hydra.utils.instantiate(cfg['input_interface'], _recursive_=False)
    #         ),
    #         "output_interface": (
    #             None
    #             if getattr(cfg, "output_interface", None) is None
    #             else hydra.utils.instantiate(cfg['output_interface'], _recursive_=False)
    #         ),
    #     }
    #     flow_instances.append(flow_with_interfaces)
    for backend_name in api_keys.keys():
        for _ in range(launcher_config["n_workers_per_key"]):
            flow_with_interfaces = {
                "flow": hydra.utils.instantiate(cfg['flow'], _recursive_=False, _convert_="partial", backend_used=backend_name),
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
