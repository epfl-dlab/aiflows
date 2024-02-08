from aiflows import flow_verse
from aiflows.backends.api_info import ApiInfo
import os
from aiflows import logging
from aiflows.utils.general_helpers import read_yaml_file, quick_load

logging.set_verbosity_debug() 

from aiflows.base_flows import BranchingFlow

dependencies = [
    {
        "url": "aiflows/ControllerExecutorFlowModule",
        "revision": "main",
    },
]

flow_verse.sync_dependencies(dependencies)
from flow_modules.aiflows.ControllerExecutorFlowModule import WikiSearchAtomicFlow
if __name__ == "__main__":

    
    root_dir = "."
    cfg_path = os.path.join(root_dir, "serve_executor.yaml")
    cfg = read_yaml_file(cfg_path)
    flow = BranchingFlow.instantiate_from_default_config(**cfg["flow"])
    
    flow.serve()