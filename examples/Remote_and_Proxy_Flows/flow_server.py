import os
from typing import Dict, Any
import aiflows
from aiflows.flow_launchers import FlowLauncher
from aiflows.base_flows import AtomicFlow
from aiflows.utils.general_helpers import read_yaml_file

import logging
from typing import List
import colink as CL
from colink import CoLink, ProtocolOperator,byte_to_int

import pickle
from reverse_number_atomic import ReverseNumberAtomicFlow


# logging.set_verbosity_debug()  # Uncomment this line to see verbose logs



def run_flow(data):
    root_dir = "."
    cfg_path = os.path.join(root_dir, "reverseNumberAtomic.yaml")
    cfg = read_yaml_file(cfg_path)

    flow_with_interfaces = {
        "flow": ReverseNumberAtomicFlow.instantiate_from_default_config(**cfg),
        "input_interface": None,
        "output_interface": None,
    }

    _, outputs = FlowLauncher.launch(
        flow_with_interfaces=flow_with_interfaces, data=data, path_to_output_file=None
    )

    flow_output_data = outputs[0][0]
    print("Output: ", flow_output_data)
    return flow_output_data


pop = ProtocolOperator(__name__)


@pop.handle("flow-protocol:flow-server")
def run_receiver(cl: CoLink, param: bytes, participants: List[CL.Participant]):

    print("Invoked receiver ", cl.get_core_addr())

    max_iters = byte_to_int(param)
    print("max_iters", max_iters)
    for i in range(max_iters):
        # Read input from initiator
        print("Waiting for input...")
        receive_data = cl.recv_variable("flow_input", participants[0])
        flow_input = pickle.loads(receive_data)
        print("Received input:", flow_input)

        # have to manually add id
        flow_input["id"] = 0

        # Run Flow
        output = run_flow(flow_input)

        # Return output
        cl.send_variable("flow_output", pickle.dumps(output), [participants[0]])


# python flow_initiator.py --addr http://127.0.0.1:2021 --jwt $(sed -n "2,2p" ./jwts.txt) --vt-public-addr 127.0.0.1
if __name__ == "__main__":
    logging.basicConfig(
        filename="flow-protocol-server.log", filemode="a", level=logging.DEBUG
    )
    print("Starting flow server worker")
    pop.run()
