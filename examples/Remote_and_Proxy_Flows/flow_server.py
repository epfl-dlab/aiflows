import os
from typing import Dict, Any
import aiflows
from aiflows.flow_launchers import FlowLauncher
from aiflows.base_flows import AtomicFlow
from aiflows.utils.general_helpers import read_yaml_file
from aiflows.messages import InputMessage
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

    
    flow = ReverseNumberAtomicFlow.instantiate_from_default_config(**cfg)
    
    input_message = InputMessage.build(data_dict=data, src_flow="TBD", dst_flow=flow.name)
        
    
    flow_output_data = flow(input_message)
      
    print("Output: ", flow_output_data)
    
    return flow_output_data.data["output_data"]


pop = ProtocolOperator(__name__)


@pop.handle("flow-protocol:flow-server")
def run_receiver(cl: CoLink, param: bytes, participants: List[CL.Participant]):

    print("Invoked receiver ", cl.get_core_addr())

    # queue_name = cl.subscribe(
    #     "_remote_storage:private:{}:flow_input".format(participants[0].user_id),
    #     None,
    # )
    # subscriber = cl.new_subscriber(queue_name)
    
    # print("queue_name", queue_name)

    max_iters = byte_to_int(param)
    

    # data = cl.read_or_wait(
    #     "_remote_storage:private:{}:flow_input".format(participants[0].user_id)
    #     )
    
    queue_name = cl.subscribe(
        "_remote_storage:private:{}:flow_input".format(participants[0].user_id),
        None,
    )
    subscriber = cl.new_subscriber(queue_name)
    

    print("max_iters", max_iters)
    for i in range(4):
        # Read input from initiator
        print("Waiting for input...")
        # update
        if i >= 1:
            data = subscriber.get_next()
            message = CL.SubscriptionMessage().FromString(data)
            print("new_message", pickle.loads(message.payload))
            breakpoint()
        # receive_data = subscriber.get_next()
   
        #flow_input = pickle.loads(data)
        #print("Received input:", data)

        # have to manually add id
        #flow_input["id"] = 0

        # Run Flow
        #output = run_flow(flow_input)
        # Return output
        #cl.send_variable("flow_output", pickle.dumps(output), [participants[0]])
        print("SENT OUTPUT", i)

# python flow_initiator.py --addr http://127.0.0.1:2021 --jwt $(sed -n "2,2p" ./jwts.txt) --vt-public-addr 127.0.0.1
if __name__ == "__main__":
    logging.basicConfig(
        filename="flow-protocol-server.log", filemode="a", level=logging.DEBUG
    )
    print("Starting flow server worker")
    pop.run()





