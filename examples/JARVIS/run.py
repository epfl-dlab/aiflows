import os

import hydra

import flows
from flows.flow_launchers import FlowLauncher
from flows.backends.api_info import ApiInfo
from flows.utils.general_helpers import read_yaml_file

from flows import logging
from flows.flow_cache import CACHING_PARAMETERS, clear_cache

CACHING_PARAMETERS.do_caching = False  # Set to True in order to disable caching
# clear_cache() # Uncomment this line to clear the cache

logging.set_verbosity_debug()

dependencies = [
    {"url": "baldwin/PyFileInterpreterFlowModule", "revision": "FlowVerse/PyFileInterpreterFlowModule"},
    {"url": "baldwin/JarvisFlowModule", "revision": "FlowVerse/JarvisFlowModule"},
    {"url": "aiflows/HumanStandardInputFlowModule","revision": "a690582584ff5345fe768e41558959a7e99bbeee"},
]
from flows import flow_verse
flow_verse.sync_dependencies(dependencies)

if __name__ == "__main__":
    # ~~~ Set the API information ~~~
    # OpenAI backend
    api_information = [ApiInfo(backend_used="openai",
                              api_key = os.getenv("OPENAI_API_KEY"))]
    # Azure backend
    # api_information = ApiInfo(backend_used = "azure",
    #                           api_base = os.getenv("AZURE_API_BASE"),
    #                           api_key = os.getenv("AZURE_OPENAI_KEY"),
    #                           api_version =  os.getenv("AZURE_API_VERSION") )

    root_dir = "examples/JARVIS"
    cfg_path = os.path.join(root_dir, "JARVISm1.3.yaml")#os.path.join(root_dir, "JARVISm1.1.yaml")
    cfg = read_yaml_file(cfg_path)
    cfg["flow"]["subflows_config"]["Controller"]["backend"]["api_infos"] = api_information
    # ~~~ Instantiate the Flow ~~~
    flow_with_interfaces = {
        "flow": hydra.utils.instantiate(cfg['flow'], _recursive_=False, _convert_="partial"),
        "input_interface": (
            None
            if cfg.get("input_interface", None) is None
            else hydra.utils.instantiate(cfg['input_interface'], _recursive_=False)
        ),
        "output_interface": (
            None
            if cfg.get( "output_interface", None) is None
            else hydra.utils.instantiate(cfg['output_interface'], _recursive_=False)
        ),
    }

    # ~~~ Get the data ~~~
    # data = {"id": 0, "goal": "Answer the following question: What is the population of Canada?"}  # Uses wikipedia
    # data = {"id": 0, "goal": "Answer the following question: Who was the NBA champion in 2023?"}  # Uses duckduckgo
    data = {"id": 0,
            "goal": "Write an email from nicolas.mario.baldwin@gmail.com to nicky.tennis.baldwin@gmail.com. \
            Introduce yourself as JARVIS, and descibe in a few senteces who you are (Jarvis from iron man). Inform him that you can now send can now send pdfs of stock prices. \
            subject of the email is 'Jarvis is getting smarter'. \
            Also, send him a plot of the microsoft stock from may 2020 till june 2021 "}
    # At first, we retrieve information about Michael Jordan the basketball player
    # If we provide feedback, only in the first round, that we are not interested in the basketball player,
    #   but the statistician, and skip the feedback in the next rounds, we get the correct answer

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
    print(flow_output_data)
