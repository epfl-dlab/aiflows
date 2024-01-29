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

def get_next_update(subscriber):
    message = CL.SubscriptionMessage().FromString(subscriber.get_next())
    while message.change_type != "update":
        message = CL.SubscriptionMessage().FromString(subscriber.get_next())

    unpickled_payload = pickle.loads(message.payload)
    input_data = unpickled_payload["data"]
    state = unpickled_payload["state"]
    return input_data,state

def send_data_to_remote(cl: CL,flow: AtomicFlow, participant: CL.Participant, output_data: Dict[str, Any]):
    
    state = flow.__getstate__(ignore_proxy_info=True)
    flow_output = {"data": output_data, "state": state}
    
    cl.remote_storage_update(
        providers = [participant.user_id],
        key = "flow_output",
        payload = pickle.dumps(flow_output),
        is_public = False,
    )

def instantiate_flow(state):
    flow_config = state["flow_config"]
    flow = ReverseNumberAtomicFlow.instantiate_from_default_config(**flow_config)
    flow.__setflowstate__(state)
    return flow

def run_flow(flow,input_data):

    input_message = InputMessage.build(data_dict=input_data, src_flow="TBD", dst_flow=flow.name)
    
    flow_output_data = flow(input_message)
    print("Output: ", flow_output_data)
    
    return flow_output_data.data["output_data"]


pop = ProtocolOperator(__name__)


@pop.handle("flow-protocol:flow-server")
def run_receiver(cl: CoLink, param: bytes, participants: List[CL.Participant]):

    print("Invoked receiver ", cl.get_core_addr())


    flow_input_qname = cl.subscribe(
        "_remote_storage:private:{}:flow_input".format(participants[0].user_id),
        None,
    )
    
    flow_input_sub = cl.new_subscriber(flow_input_qname)
    
    cl.remote_storage_create(
        providers = [participants[0].user_id],
        key = "flow_output",
        payload = "",
        is_public = False,
    )
    
    print("Waiting for input...")
    
    input_data,state = get_next_update(flow_input_sub)
    flow = instantiate_flow(state)
    output = run_flow(flow,input_data=input_data)
    
    send_data_to_remote(cl,flow, participants[0], output)
        # receive_data = subscriber.get_next()
   
        #flow_input = pickle.loads(data)
        #print("Received input:", data)

        # have to manually add id
        #flow_input["id"] = 0

        # Run Flow
        #
        # Return output
        #cl.send_variable("flow_output", pickle.dumps(output), [participants[0]])
  

# python flow_initiator.py --addr http://127.0.0.1:2021 --jwt $(sed -n "2,2p" ./jwts.txt) --vt-public-addr 127.0.0.1
if __name__ == "__main__":
    logging.basicConfig(
        filename="flow-protocol-server.log", filemode="a", level=logging.DEBUG
    )
    print("Starting flow server worker")
    pop.run()





