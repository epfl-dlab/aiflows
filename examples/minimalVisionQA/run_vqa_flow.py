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

logging.set_verbosity_debug()  # Uncomment this line to see verbose logs

from aiflows import flow_verse

dependencies = [
    {"url": "aiflows/VisionFlowModule", "revision": "main"},
]
flow_verse.sync_dependencies(dependencies)

if __name__ == "__main__":
    # ~~~ Set the API information ~~~
    # OpenAI backend

    api_information = [ApiInfo(backend_used="openai", api_key=os.getenv("OPENAI_API_KEY"))]

    # # Azure backend
    # api_information = ApiInfo(backend_used = "azure",
    #                           api_base = os.getenv("AZURE_API_BASE"),
    #                           api_key = os.getenv("AZURE_OPENAI_KEY"),
    #                           api_version =  os.getenv("AZURE_API_VERSION") )
    
    FLOW_MODULES_PATH = "./"
    
    jwt = os.getenv("COLINK_JWT")
    addr = os.getenv("LOCAL_COLINK_ADDRESS")
    
    cl = serve_utils.start_colink_component(
        "Reverse Number Demo",
        {"jwt": jwt, "addr": addr}
    )

    root_dir = "."
    cfg_path = os.path.join(root_dir, "visionQA.yaml")
    cfg = read_yaml_file(cfg_path)

    serve_utils.recursive_serve_flow(
        cl = cl,
        flow_type="simpleQA_served",
        default_config=cfg,
        default_state=None,
        default_dispatch_point="coflows_dispatch",
    )
    
    #in case you haven't started the dispatch worker thread, uncomment
    run_dispatch_worker_thread(cl, dispatch_point="coflows_dispatch", flow_modules_base_path=FLOW_MODULES_PATH)
    
    # put api information in config (done like this for privacy reasons)
    quick_load_api_keys(cfg, api_information, key="api_infos")
    
    proxy_flow = serve_utils.recursive_mount(
        cl=cl,
        client_id="local",
        flow_type="simpleQA_served",
        config_overrides=cfg,
        initial_state=None,
        dispatch_point_override=None,
    )   
    
    url_image = {
        "type": "url",
        "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Gfp-wisconsin-madison-the-nature-boardwalk.jpg/2560px-Gfp-wisconsin-madison-the-nature-boardwalk.jpg",
    }
    local_image = {"type": "local_path", "image": os.path.join(root_dir, "wikimedia_desert_image.png")}
    video = {
        "video_path": os.path.join(root_dir, "Bison.mp4"),
        "resize": 768,
        "frame_step_size": 30,
        "start_frame": 0,
        "end_frame": None,
    }

    # ~~~ Get the data ~~~
    # data = {"id": 0, "question": "What are in these images? Is there any difference between them?",  "data": {"images": [url_image,local_image]}}  # This can be a list of samples
    data = {
        "id": 0,
        "question": "What’s in this image?",
        "data": {"images": [url_image]},
    }  # This can be a list of samples
    # data = {"id": 0,
    #         "question": "These are frames from a video that I want to upload. Generate a compelling description that I can upload along with the video.",
    #         "data": {"video": video}}  # This can be a list of samples

    # ~~~ Run inference ~~~
    input_message = FlowMessage(
        data= data,
        src_flow="Coflows team",
        dst_flow=proxy_flow,
        is_input_msg=True
    )
    
    future = proxy_flow.ask(input_message)
    
    print(future.get_data())
