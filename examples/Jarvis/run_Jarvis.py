import os

import hydra

from aiflows.backends.api_info import ApiInfo
from aiflows.messages import InputMessage
from aiflows.utils.general_helpers import read_yaml_file
from aiflows.utils.general_helpers import quick_load

from aiflows import logging
from aiflows.flow_cache import CACHING_PARAMETERS, clear_cache

CACHING_PARAMETERS.do_caching = False  # Set to True in order to disable caching
# clear_cache() # Uncomment this line to clear the cache

logging.set_verbosity_debug()
logging.auto_set_dir()

dependencies = [
    {"url": "aiflows/HumanStandardInputFlowModule", "revision": "4ff043522c89a964ea3a928ce09811c51a2b5b98"},
    {"url": "aiflows/ChatFlowModule", "revision": "297c90d08087d9ff3139521f11d1a48d7dc63ed4"},
    {"url": "aiflows/AbstractBossFlowModule", "revision": "main"},
    {"url": "aiflows/MemoryReadingFlowModule", "revision": "main"},
    {"url": "aiflows/PlanWriterFlowModule", "revision": "main"},
    {"url": "aiflows/ExtendLibraryFlowModule", "revision": "main"},
    {"url": "aiflows/RunCodeFlowModule", "revision": "main"},
    {"url": "aiflows/ReplanningFlowModule", "revision": "main"},
    {"url": "aiflows/CoderFlowModule", "revision": "main"},
    {"url": "aiflows/JarvisFlowModule", "revision": "main"},
]

from aiflows import flow_verse

flow_verse.sync_dependencies(dependencies)

def set_up_memfiles(cfg):
    code_lib_file_loc = os.path.join(current_dir, "library.py")
    jarvis_plan_file_loc = os.path.join(current_dir, "plan_jarvis.txt")
    jarvis_logs_file_loc = os.path.join(current_dir, "logs_jarvis.txt")
    coder_plan_file_loc = os.path.join(current_dir, "plan_coder.txt")
    coder_logs_file_loc = os.path.join(current_dir, "logs_coder.txt")
    extlib_plan_file_loc = os.path.join(current_dir, "plan_extlib.txt")
    extlib_logs_file_loc = os.path.join(current_dir, "logs_extlib.txt")
    with open(code_lib_file_loc, 'w') as file:
         pass
    with open(jarvis_plan_file_loc, 'w') as file:
        pass
    with open(jarvis_logs_file_loc, 'w') as file:
        pass
    with open(coder_plan_file_loc, 'w') as file:
        pass
    with open(coder_logs_file_loc, 'w') as file:
        pass
    with open(extlib_plan_file_loc, 'w') as file:
        pass
    with open(extlib_logs_file_loc, 'w') as file:
        pass

    memfiles_jarvis = {}
    memfiles_coder = {}
    memfiles_extlib = {}
    memfiles_writecode_interactivecoder = {}
    memfiles_writecode_test = {}
    memfiles_jarvis["plan"] = jarvis_plan_file_loc
    memfiles_jarvis["logs"] = jarvis_logs_file_loc
    memfiles_coder["plan"] = coder_plan_file_loc
    memfiles_coder["logs"] = coder_logs_file_loc
    memfiles_coder["code_library"] = code_lib_file_loc
    memfiles_extlib["plan"] = extlib_plan_file_loc
    memfiles_extlib["logs"] = extlib_logs_file_loc
    memfiles_extlib["code_library"] = code_lib_file_loc
    memfiles_writecode_interactivecoder["code_library"] = code_lib_file_loc
    memfiles_writecode_test["code_library"] = code_lib_file_loc
    cfg["memory_files"] = memfiles_jarvis
    cfg["subflows_config"]["CtrlExMem"]["subflows_config"]["Executor"]["subflows_config"]["Coder"]["memory_files"] = memfiles_coder
    cfg["subflows_config"]["CtrlExMem"]["subflows_config"]["Executor"]["subflows_config"]["Coder"]["subflows_config"]["CtrlExMem"]["subflows_config"]["Executor"]["subflows_config"]["extend_library"]["memory_files"] = memfiles_extlib
    cfg["subflows_config"]["CtrlExMem"]["subflows_config"]["Executor"]["subflows_config"]["Coder"]["subflows_config"]["CtrlExMem"]["subflows_config"]["Executor"]["subflows_config"]["extend_library"]["subflows_config"]["CtrlExMem"]["subflows_config"]["Executor"]["subflows_config"]["write_code"][
        "subflows_config"]["Executor"]["subflows_config"]["write_code"][
        "memory_files"] = memfiles_writecode_interactivecoder
    cfg["subflows_config"]["CtrlExMem"]["subflows_config"]["Executor"]["subflows_config"]["Coder"]["subflows_config"]["CtrlExMem"]["subflows_config"]["Executor"]["subflows_config"]["extend_library"]["subflows_config"]["CtrlExMem"]["subflows_config"]["Executor"]["subflows_config"]["write_code"][
        "subflows_config"]["Executor"]["subflows_config"]["test"]["memory_files"] = memfiles_writecode_test


if __name__ == "__main__":
    # ~~~ make sure to set the openai api key in the envs ~~~
    key = os.getenv("OPENAI_API_KEY")
    api_information = [ApiInfo(backend_used="openai", api_key=os.getenv("OPENAI_API_KEY"))]
    path_to_output_file = None

    current_dir = os.getcwd()
    cfg_path = os.path.join(current_dir, "JarvisFlow.yaml")
    cfg = read_yaml_file(cfg_path)

    # ~~~ setting api information into config ~~~
    quick_load(cfg, api_information)

    # ~~~ setting memory files into config ~~~
    set_up_memfiles(cfg)

    # ~~~ instantiating the flow and input data ~~~
    JarvisFlow = hydra.utils.instantiate(cfg, _recursive_=False, _convert_="partial")
    input_data = {
        "goal": "Download tesla's stock prices from 2022-01-01 to 2022-06-01, plot the prices."
     }
    input_message = InputMessage.build(
        data_dict=input_data,
        src_flow="Launcher",
        dst_flow=JarvisFlow.name
    )

    # ~~~ calling the flow ~~~
    output_message = JarvisFlow(input_message)

    # ~~~ printing the output ~~~
    print(output_message)