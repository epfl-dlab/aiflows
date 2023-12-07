from flows.backends.api_info import ApiInfo
from flows.utils.general_helpers import find_replace_in_dict
from flows.flow_launchers import FlowLauncher
from flows.backends.api_info import ApiInfo
from flows import flow_verse
import os 
from flows import logging
from flows.utils.general_helpers import read_yaml_file


dependencies = [
    {"url": "aiflows/ChatFlowModule", "revision": "main"}
]

flow_verse.sync_dependencies(dependencies)
logging.set_verbosity_debug()

from flow_modules.aiflows.ChatFlowModule import ChatAtomicFlow

if __name__ == "__main__":

    # ~~~ Set the API information ~~~
    #openai backend
    api_information = [ApiInfo(backend_used="openai", api_key=os.getenv("OPENAI_API_KEY"))]
    # api_information = ApiInfo(backend_used = "azure",
    #                           api_base = os.getenv("AZURE_API_BASE"),
    #                           api_key = os.getenv("AZURE_OPENAI_KEY"),
    #                           api_version =  os.getenv("AZURE_API_VERSION") ) 
    
    # get demo configuration
    cfg = read_yaml_file("flow_modules/aiflows/ChatFlowModule/demo.yaml")

    # put the API information in the config
    cfg["flow"]["backend"]["api_infos"] = api_information

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