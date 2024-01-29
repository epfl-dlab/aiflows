import logging
from typing import List
import colink as CL
from colink import CoLink, ProtocolOperator, decode_jwt_without_validation

import aiflows
from aiflows.flow_launchers import FlowLauncher
from aiflows.base_flows import SequentialFlow
from aiflows import flow_verse

import pickle
from omegaconf import OmegaConf


# logging.set_verbosity_debug()  # Uncomment this line to see verbose logs

pop = ProtocolOperator(__name__)


@pop.handle("flow-protocol:flow-initiator")
def run_initiator(cl: CoLink, param: bytes, participants: List[CL.Participant]):
    print("Invoked Initiator", cl.get_core_addr())

    print("TASK_ID", cl.get_task_id())
    # Read user input
    print("Reading user input...")
    user_input_bytes = cl.read_or_wait(f"tasks:{cl.get_task_id()}:user_input")
    user_input = pickle.loads(user_input_bytes)
    print("User input:", user_input)
    # Read flow config
    print("Reading config...")
    cfg_bytes = cl.read_or_wait(f"tasks:{cl.get_task_id()}:flow_cfg")
    cfg = OmegaConf.create(pickle.loads(cfg_bytes))
    cfg_container = OmegaConf.to_container(cfg, resolve=True)
    cfg_container["task_id"] = cl.get_task_id()
    # Instantiate Flow
    flow = SequentialFlow.instantiate_from_default_config(**cfg_container)

    # Launch Flow
    print("Launching flow...")
    _, outputs = FlowLauncher.launch(
        flow_with_interfaces={"flow": flow},
        data=user_input,
        path_to_output_file=None,
        cl =cl
    )

    flow_output_data = outputs[0]
    print("Completed! ", flow_output_data)

    # Write output to user's private storage
    cl.create_entry(
        "tasks:{}:output".format(cl.get_task_id()), pickle.dumps(flow_output_data)
    )


# python flow_initiator.py --addr http://127.0.0.1:2021 --jwt $(sed -n "1,1p" ./jwts.txt) --vt-public-addr 127.0.0.1
if __name__ == "__main__":
    logging.basicConfig(
        filename="flow-protocol-initiator.log", filemode="a", level=logging.DEBUG
    )

    print("Starting initiator worker")
    pop.run()
