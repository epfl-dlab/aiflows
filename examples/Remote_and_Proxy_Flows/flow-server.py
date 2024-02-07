from aiflows import flow_verse
from aiflows.backends.api_info import ApiInfo
import os
from aiflows import logging
from aiflows.utils.general_helpers import read_yaml_file, quick_load

logging.set_verbosity_debug() 
# flows that can be served
dependencies = [
    {
        "url": "aiflows/ChatFlowModule",
        "revision": "297c90d08087d9ff3139521f11d1a48d7dc63ed4",
    },
]
flow_verse.sync_dependencies(dependencies)

from flow_modules.aiflows.ChatFlowModule import ChatAtomicFlow

if __name__ == "__main__":
    api_information = [
        ApiInfo(backend_used="openai", api_key=os.getenv("OPENAI_API_KEY"))
    ]
    
    root_dir = "."
    cfg_path = os.path.join(root_dir, "chatflowserver.yaml")
    cfg = read_yaml_file(cfg_path)
    quick_load(cfg, api_information, key="api_infos")
    flow = ChatAtomicFlow.instantiate_from_default_config(**cfg["flow"])
    
    flow.serve()