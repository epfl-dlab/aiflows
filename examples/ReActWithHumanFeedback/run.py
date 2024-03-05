import os

import hydra

import aiflows
from aiflows.flow_launchers import FlowLauncher
from aiflows.backends.api_info import ApiInfo
from aiflows.utils.general_helpers import read_yaml_file, quick_load_api_keys

from aiflows import logging
from aiflows.flow_cache import CACHING_PARAMETERS, clear_cache
from aiflows.utils import serve_utils
from aiflows.workers import run_dispatch_worker_thread
from aiflows.messages import FlowMessage
from aiflows.interfaces import KeyInterface

CACHING_PARAMETERS.do_caching = False  # Set to True in order to disable caching
# clear_cache() # Uncomment this line to clear the cache

logging.set_verbosity_debug()

from aiflows import flow_verse
# ~~~ Load Flow dependecies from FlowVerse ~~~
dependencies = [
    {"url": "aiflows/ControllerExecutorFlowModule", "revision": "coflows"},
    {"url": "aiflows/HumanStandardInputFlowModule", "revision": "main"},
    {"url": "aiflows/LCToolFlowModule", "revision": "main"},
]

flow_verse.sync_dependencies(dependencies)

if __name__ == "__main__":
    # ~~~ Set the API information ~~~
    # OpenAI backend
    api_information = [ApiInfo(backend_used="openai", api_key=os.getenv("OPENAI_API_KEY"))]
    # Azure backend
    # api_information = [ApiInfo(backend_used = "azure",
    #                           api_base = os.getenv("AZURE_API_BASE"),
    #                           api_key = os.getenv("AZURE_OPENAI_KEY"),
    #                           api_version =  os.getenv("AZURE_API_VERSION") )]

    FLOW_MODULES_PATH = "./"
    
    jwt = os.getenv("COLINK_JWT")
    addr = os.getenv("LOCAL_COLINK_ADDRESS")
    
    cl = serve_utils.start_colink_component(
        "Reverse Number Demo",
        {"jwt": jwt, "addr": addr}
    )
    # path_to_output_file = "output.jsonl"  # Uncomment this line to save the output to disk

    root_dir = "."
    cfg_path = os.path.join(root_dir, "ReActWithHumanFeedback.yaml")
    cfg = read_yaml_file(cfg_path)
    # put the API information in the config
    serve_utils.recursive_serve_flow(
        cl = cl,
        flow_type="ReActWithHumanFeedback_served",
        default_config=cfg,
        default_state=None,
        default_dispatch_point="coflows_dispatch",
    )
    
    run_dispatch_worker_thread(cl, dispatch_point="coflows_dispatch", flow_modules_base_path=FLOW_MODULES_PATH)
    run_dispatch_worker_thread(cl, dispatch_point="coflows_dispatch", flow_modules_base_path=FLOW_MODULES_PATH)

    quick_load_api_keys(cfg, api_information, key="api_infos")

    # ~~~ Get the data ~~~
    # This can be a list of samples
    # data = {"id": 0, "goal": "Answer the following question: What is the population of Canada?"}  # Uses wikipedia
    # data = {"id": 0, "goal": "Answer the following question: Who was the NBA champion in 2023?"}
    data = {
        "id": 0,
        "goal": "Answer the following question: What is the profession and date of birth of Michael Jordan?",
    }
    # ~~~ Run inference ~~~
    proxy_flow = serve_utils.recursive_mount(
        cl=cl,
        client_id="local",
        flow_type="ReActWithHumanFeedback_served",
        config_overrides=cfg,
        initial_state=None,
        dispatch_point_override=None,
    )   
    # ~~~ Print the output ~~~
    input_message = FlowMessage(
        data= data,
        src_flow="Coflows team",
        dst_flow=proxy_flow,
        is_input_msg=True
    )
    
    future = proxy_flow.ask(input_message)
    
    print(future.get_data())

