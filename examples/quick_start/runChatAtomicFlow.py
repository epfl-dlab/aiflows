from aiflows.flow_launchers import FlowLauncher
from aiflows.backends.api_info import ApiInfo
from aiflows import flow_verse
from aiflows import logging
from aiflows.utils.general_helpers import read_yaml_file, quick_load


dependencies = [
    {"url": "aiflows/ChatFlowModule", "revision": "main"}
]

flow_verse.sync_dependencies(dependencies)
logging.set_verbosity_debug()

from flow_modules.aiflows.ChatFlowModule import ChatAtomicFlow

if __name__ == "__main__":

    # ~~~ Set the API information ~~~
    #OpenAI backend
    api_key = "" # copy paste your api key here
    api_information = [ApiInfo(backend_used="openai", api_key=api_key)]

    # Azure backend
    # api_key = "" # copy paste your api key here
    # api_base = "" # copy paste your api base here
    # api_version = "" #copypase your api base here
    # api_information = ApiInfo(backend_used = "azure",
    #                           api_base =api_base,
    #                           api_key = api_version,
    #                           api_version =  api_version )
    
    # get demo configuration
    cfg = read_yaml_file("flow_modules/aiflows/ChatFlowModule/demo.yaml")

    # put the API information in the config
    quick_load(cfg, api_information, key="api_infos")

    # ~~~ Instantiate the Flow ~~~
    flow = ChatAtomicFlow.instantiate_from_default_config(**cfg["flow"])    
    flow_with_interfaces = {
        "flow": flow,
        "input_interface": None,
        "output_interface": None,
    }
    
    # ~~~ Get the data ~~~
    data = {"id": 0, "question": "What is the capital of France?"} 

    # ~~~ Run the Flow ~~~
    _, outputs  = FlowLauncher.launch(
            flow_with_interfaces= flow_with_interfaces ,data=data
        )
     # ~~~ Print the output ~~~
    flow_output_data = outputs[0]
    print(flow_output_data)