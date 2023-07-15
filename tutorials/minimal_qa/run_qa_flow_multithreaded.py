import os

import hydra.utils

from flows import logging
from flows.datasets import OutputsDataset
from flows.flow_cache import CACHING_PARAMETERS, clear_cache
from flows.flow_launchers import FlowMultiThreadedAPILauncher

CACHING_PARAMETERS.do_caching = False  # Set to false to disable caching
# clear_cache() # Uncomment this line to clear the cache

from flows.flow_launchers import FlowLauncher

# logging.set_verbosity_debug()  # Uncomment this line to see verbose logs


from flows import flow_verse
from flows.utils.general_helpers import read_yaml_file

dependencies = [
    {"url": "martinjosifoski/OpenAIChatAtomicFlow", "revision": "921cf6a54be33ca9ad4f336827699616f7ea75d1"},
]
flow_verse.sync_dependencies(dependencies)

from martinjosifoski.OpenAIChatAtomicFlow import OpenAIChatAtomicFlow


if __name__ == "__main__":
    root_dir = "."

    # ~~~ Launcher Configuration ~~~
    output_dir = "predictions"
    api_keys = [os.getenv("OPENAI_API_KEY")]

    launcher_config = {
        "api_keys": api_keys,
        "single_threaded": True,
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
    overrides_config = read_yaml_file(cfg_path)

    if launcher_config["single_threaded"]:
        n_workers = 1
    else:
        n_workers = launcher_config["n_workers_per_key"] * len(api_keys)
    # We can initialize the flow with hydra (we need to add the target in the yaml in that case)
    # flows = [hydra.utils.instantiate(overrides_config, _convert_="partial", _recursive_=False)
    #          for _ in range(n_workers)]
    # or
    flows = [OpenAIChatAtomicFlow.instantiate_from_default_config(overrides=overrides_config) for _ in range(n_workers)]

    # ~~~ Get the data ~~~
    data = [{"id": 0, "question": "What is the capital of France?"},
            {"id": 1, "question": "What is the capital of Germany?"}]

    # ~~~ Run inference ~~~
    launcher = FlowMultiThreadedAPILauncher(flow=flows,
                                            **launcher_config)
    launcher.predict_dataloader(data)

    # ~~~ Print the output ~~~
    output_dataset = OutputsDataset(data_dir=output_dir)
    for output in output_dataset:
        print("~~~", "ID: ", output["id"], "~~~")
        print(output_dataset.get_output_data(output, idx=0))
