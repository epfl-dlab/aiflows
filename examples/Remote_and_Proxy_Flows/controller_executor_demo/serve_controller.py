from aiflows import flow_verse
from aiflows.backends.api_info import ApiInfo
import os
from aiflows import logging
from aiflows.utils.general_helpers import read_yaml_file, quick_load

logging.set_verbosity_debug() 

dependencies = [
    {
        "url": "aiflows/ControllerExecutorFlowModule",
        "revision": "main",
    },
]

flow_verse.sync_dependencies(dependencies)

from flow_modules.aiflows.ControllerExecutorFlowModule import ControllerAtomicFlow

if __name__ == "__main__":
    api_information = [
        ApiInfo(backend_used="openai", api_key=os.getenv("OPENAI_API_KEY"))
    ]
    
    root_dir = "."
    cfg_path = os.path.join(root_dir, "serve_controller.yaml")
    cfg = read_yaml_file(cfg_path)
    quick_load(cfg, api_information, key="api_infos")
    flow = ControllerAtomicFlow.instantiate_from_default_config(**cfg["flow"])
    
    flow.serve()