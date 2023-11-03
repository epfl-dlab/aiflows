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
logging.auto_set_dir()

dependencies = [
    {"url": "aiflows/ControllerExecutorFlowModule", "revision": "ba2c90bb9b0539af39ccad90c98a2ba1f9a22c91"},
    {"url": "aiflows/HumanStandardInputFlowModule", "revision": "890e92da1fefbae642fd84296e31bca7f61ea710"},
    {"url": "aiflows/LCToolFlowModule", "revision": "46dd24ecc3dc4f4f0191e57c202cc7d20e8e7782"},
]
from flows import flow_verse

flow_verse.sync_dependencies(dependencies)
from ReActWithHumanFeedback import ReActWithHumanFeedback

if __name__ == "__main__":
    # ~~~ Set the API information ~~~
    # OpenAI backend
    # api_information = ApiInfo("openai", os.getenv("OPENAI_API_KEY"))
    # Azure backend
    api_information = ApiInfo("azure", os.getenv("AZURE_OPENAI_KEY"), os.getenv("AZURE_OPENAI_ENDPOINT"))

    path_to_output_file = None
    # path_to_output_file = "output.jsonl"  # Uncomment this line to save the output to disk

    # ~~~ Instantiate the Flow ~~~
    flow_with_interfaces = {
        "flow": ReActWithHumanFeedback.instantiate_from_default_config(),
        "input_interface": None,
        "output_interface": None,
    }

    # ~~~ Get the data ~~~
    # This can be a list of samples
    # data = {"id": 0, "goal": "Answer the following question: What is the population of Canada?"}  # Uses wikipedia
    # data = {"id": 0, "goal": "Answer the following question: Who was the NBA champion in 2023?"}  # Uses duckduckgo
    data = {"id": 0, "goal": "Answer the following question: What is the profession and date of birth of Michael Jordan?"}
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
        api_information=api_information,
    )

    # ~~~ Print the output ~~~
    flow_output_data = outputs[0]
    print(flow_output_data)
