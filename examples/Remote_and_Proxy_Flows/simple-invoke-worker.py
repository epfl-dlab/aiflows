from aiflows.utils.colink_protocol_utils import get_simple_invoke_protocol
import sys

from aiflows import flow_verse
from aiflows.backends.api_info import ApiInfo
from aiflows.utils.general_helpers import read_yaml_file, quick_load
import os

def create_flow():
    # flows that can be served
    dependencies = [
        {
            "url": "aiflows/ChatFlowModule",
            "revision": "297c90d08087d9ff3139521f11d1a48d7dc63ed4",
        },
    ]
    flow_verse.sync_dependencies(dependencies)

    from flow_modules.aiflows.ChatFlowModule import ChatAtomicFlow


    api_information = [
        ApiInfo(backend_used="openai", api_key=os.getenv("OPENAI_API_KEY"))
    ]
    
    root_dir = "."
    cfg_path = os.path.join(root_dir, "chatflowserver.yaml")
    cfg = read_yaml_file(cfg_path)
    quick_load(cfg, api_information, key="api_infos")
    flow = ChatAtomicFlow.instantiate_from_default_config(**cfg["flow"])
    
    return flow


# python simple-invoke-worker.py --addr http://127.0.0.1:2021 --jwt $(sed -n "1,1p" ./jwts.txt) --vt-public-addr 127.0.0.1
if __name__ == "__main__":
    pop = get_simple_invoke_protocol(__name__, ephemeral_flow_create=create_flow)
    print("Starting simple-invoke-worker for user", sys.argv[4], "\n")
    pop.run()