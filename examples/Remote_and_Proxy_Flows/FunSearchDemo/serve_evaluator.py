from aiflows.utils.colink_protocol_utils import ephemeral_serve
from aiflows.utils.general_helpers import read_yaml_file
import sys


def create_flow(flow_config):
    from aiflows import flow_verse
    
    dependencies = [
        {"url": "aiflows/EvaluatorFlowModule", "revision": "../FunSearch/EvaluatorFlowModule"},
    ]
    flow_verse.sync_dependencies(dependencies)
    from flow_modules.aiflows.EvaluatorFlowModule import EvaluatorFlow
    
    flow = EvaluatorFlow.instantiate_from_default_config(**flow_config)
    
    return flow




if __name__ == "__main__":
        
    colink_info = read_yaml_file("./colink_info_user_1.yaml")["colink_info"]
   
    colink_info["input_queue_name"] =  "EvaluatorInputQueue"
    colink_info["load_incoming_states"] = False
    
    ephemeral_serve(colink_info, create_flow)