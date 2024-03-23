
from aiflows.backends.api_info import ApiInfo
from aiflows.utils.general_helpers import read_yaml_file, quick_load_api_keys

from aiflows import logging
from aiflows.flow_cache import CACHING_PARAMETERS, clear_cache

from aiflows.utils import serve_utils
from aiflows.workers import run_dispatch_worker_thread
from aiflows.messages import FlowMessage
from aiflows.interfaces import KeyInterface
from aiflows.utils.colink_utils import start_colink_server
from aiflows.workers import run_dispatch_worker_thread

CACHING_PARAMETERS.do_caching = False  # Set to True in order to disable caching
# clear_cache() # Uncomment this line to clear the cache

logging.set_verbosity_debug()


dependencies = [
    {"url": "aiflows/ChatFlowModule", "revision": "main"},
]

from aiflows import flow_verse
flow_verse.sync_dependencies(dependencies)

if __name__ == "__main__":

    #1. ~~~~~ Set up a colink server ~~~~
    
    cl = start_colink_server()
    
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
    quick_load_api_keys(cfg, api_information, key="api_infos")

    #3. ~~~~ Serve The Flow ~~~~
    serve_utils.serve_flow(
        cl = cl,
        flow_class_name="flow_modules.aiflows.ChatFlowModule.ChatAtomicFlow",
        flow_endpoint="simpleQA",
    )    
    
    #4. ~~~~~Start A Worker Thread~~~~~
    run_dispatch_worker_thread(cl)

    #5. ~~~~~Mount the flow and get its proxy~~~~~~
    proxy_flow= serve_utils.get_flow_instance(
        cl=cl,
        flow_endpoint="simpleQA",
        user_id="local",
        config_overrides = cfg
    ) 
    
    #6. ~~~ Get the data ~~~
    data = {"id": 0, "question": "What is the capital of France?"}  # This can be a list of samples
   
       
    input_message = proxy_flow.package_input_message(data = data)
    
    #7. ~~~ Run inference ~~~
    future = proxy_flow.get_reply_future(input_message)
    
    #uncomment this line if you would like to get the full message back
    #reply_message = future.get_message()
    reply_data = future.get_data()
    
    # ~~~ Print the output ~~~
    print("~~~~~~Reply~~~~~~")
    print(reply_data)