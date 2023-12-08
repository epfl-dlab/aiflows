import os

import hydra

import aiflows
from aiflows.flow_launchers import FlowLauncher
from aiflows.backends.api_info import ApiInfo
from aiflows.utils.general_helpers import read_yaml_file

from aiflows import logging
from aiflows.flow_cache import CACHING_PARAMETERS, clear_cache

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

    root_dir = "."
    cfg_path = os.path.join(root_dir, "visionQA.yaml")
    cfg = read_yaml_file(cfg_path)

    cfg["flow"]["backend"]["api_infos"] = api_information

    # ~~~ Instantiate the Flow ~~~
    flow_with_interfaces = {
        "flow": hydra.utils.instantiate(cfg["flow"], _recursive_=False, _convert_="partial"),
        "input_interface": (
            None
            if cfg.get("input_interface", None) is None
            else hydra.utils.instantiate(cfg["input_interface"], _recursive_=False)
        ),
        "output_interface": (
            None
            if cfg.get("output_interface", None) is None
            else hydra.utils.instantiate(cfg["output_interface"], _recursive_=False)
        ),
    }
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
    path_to_output_file = None
    # path_to_output_file = "output.jsonl"  # Uncomment this line to save the output to disk

    _, outputs = FlowLauncher.launch(
        flow_with_interfaces=flow_with_interfaces, data=data, path_to_output_file=path_to_output_file
    )

    # ~~~ Print the output ~~~
    flow_output_data = outputs[0]
    print(flow_output_data)
