
from aiflows.utils.colink_protocol_utils import get_simple_invoke_protocol
from aiflows.utils.general_helpers import read_yaml_file
import aiflows
import sys
import colink
import os
import hydra
from aiflows import flow_verse

dependencies = [
    {
        "url": "aiflows/ControllerExecutorFlowModule",
        "revision": "main",
    },
]

flow_verse.sync_dependencies(dependencies)

from flow_modules.aiflows.ControllerExecutorFlowModule import ControllerExecutorFlow

def create_circular():
    root_dir = "."
    cfg_path = os.path.join(root_dir, "controller_executor_flow_ephemeral.yaml")
    cfg = read_yaml_file(cfg_path)
    flow = hydra.utils.instantiate(cfg,_recursive_=False, _convert_="partial")
    return flow

# python circular_flow_ephemeral.py --addr http://127.0.0.1:2021 --jwt $(sed -n "2,2p" ../jwts.txt) --vt-public-addr 127.0.0.1
if __name__ == "__main__":
    pop = get_simple_invoke_protocol(__name__, ephemeral_flow_create=create_circular)
    print("Starting simple-invoke-worker for user", sys.argv[4], "\n")
    pop.run()