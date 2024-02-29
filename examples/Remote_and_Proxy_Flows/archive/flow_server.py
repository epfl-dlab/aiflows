import os
from typing import Dict, Any
import aiflows
from aiflows.flow_launchers import FlowLauncher
from aiflows.base_flows import AtomicFlow, SequentialFlow
from QueueFlow import QueueFlow
from aiflows.utils.general_helpers import read_yaml_file
from aiflows.messages import InputMessage
import logging
from typing import List
import colink as CL
from colink import CoLink, ProtocolOperator, byte_to_int
import pickle
from reverse_number_atomic import ReverseNumberAtomicFlow

    
def get_queue_subscriptions(cl: CL, participants: List[CL.Participant]):
    subscriptions = {}
    curr_participant_index = cl.get_participant_index(participants)
    for i,participant in enumerate(participants):
        if i != curr_participant_index:
            print("fetching subscriptions of participant with role ",participant.role ,".....")
            qname = \
                cl.subscribe("_remote_storage:private:{}:flow_data".format(participant.user_id), None)
            
            subscriber = cl.new_subscriber(qname)
            subscriptions[participant.user_id] = subscriber
            
            #create a remote storage on the other side
            cl.remote_storage_create(
                providers = [participant.user_id],
                key = "flow_data",
                payload = "",
                is_public = False,
            )
            print("fetched !!!")
        
    return subscriptions

def instantiate_remote_flow( subscriptions , participants):
    
    subflow = ReverseNumberAtomicFlow.instantiate_from_default_config()
    subflow_name = {subflow.flow_config['name']}
    overrides = {
        "name": f"queue_flow_{subflow_name}",
        "subflows_config": subflow.flow_config
    }
    
    queue_name_config = QueueFlow.get_config(**overrides)
    queueflow = QueueFlow(
        flow_config=queue_name_config,
        subflows=[subflow],
        subscriptions=subscriptions,
        participants=participants
    )
    
    #the most classic topology (This would change for more complex flows).
    # For example, Sampler in FunSearch
    topology =  [
        {
            "goal": "pull data",
            "input_interface": {"_target_": "aiflows.interfaces.KeyInterface"},
            "flow": "queueFlow",
            "action": "pull_from_queue",
            "participants": ["flow-initiator"],
            "output_interface": {"_target_": "aiflows.interfaces.KeyInterface"},
        },
        {
            "goal": "run flow",
            "input_interface": {"_target_": "aiflows.interfaces.KeyInterface"},
            "flow": "queueFlow",
            "action": "call",
            "output_interface": {"_target_": "aiflows.interfaces.KeyInterface"},
        },
        {
            "goal": "send back output",
            "input_interface": {"_target_": "aiflows.interfaces.KeyInterface"},
            "flow": "queueFlow",
            "action": "push_to_queue",
            "participants": ["flow-initiator"],
            "output_interface": {"_target_": "aiflows.interfaces.KeyInterface"}
        }
    ]
    
    sequential_flow_config = SequentialFlow.get_config(**overrides)
    sequential_flow_config["subflows_config"] = {"queueFlow": queueflow.flow_config}
    sequential_flow_config["topology"] = topology
    
    #mock interface for the moment
    sequential_flow_config["input_interface"] = ["id"]
    sequential_flow_config["output_interface"] = ["id"]
    flow = SequentialFlow(flow_config=sequential_flow_config,subflows={"queueFlow": queueflow})
    return flow

def run_flow(flow,input_data,cl):

    input_message = InputMessage.build(data=input_data, src_flow="TBD", dst_flow=flow.name)
    
    flow_output_data = flow(input_message,cl=cl)
    print("Output: ", flow_output_data)
    
    return flow_output_data.data["output_data"]

pop = ProtocolOperator(__name__)

@pop.handle("flow-protocol:flow-server")
def run_receiver(cl: CoLink, param: bytes, participants: List[CL.Participant])

    print("Invoked receiver ", cl.get_core_addr())
    
    print("fetching subscriptions...")
    
    subscriptions = get_queue_subscriptions(cl, participants)
    
    print("instantiating flow...")
    
    flow  = instantiate_remote_flow(subscriptions , participants)
    
    input_data = {"id": 0}
    
    print("running flow...")
    
    run_flow(flow,input_data,cl)
    
# python flow_initiator.py --addr http://127.0.0.1:2021 --jwt $(sed -n "2,2p" ./jwts.txt) --vt-public-addr 127.0.0.1
if __name__ == "__main__":
    logging.basicConfig(
        filename="flow-protocol-server.log", filemode="a", level=logging.DEBUG
    )
    print("Starting flow server worker")
    pop.run()