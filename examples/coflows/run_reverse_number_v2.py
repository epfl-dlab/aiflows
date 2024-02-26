import argparse
import os

from aiflows.utils import serve_utils
from aiflows.utils.coflows_utils import ask_flow
from aiflows.utils.general_helpers import read_yaml_file
from aiflows.utils import logging
logging.set_verbosity_debug()
import hydra
import sys
from aiflows.base_flows import AtomicFlow
FLOW_MODULES_PATH = "./"

def parse_args():
    parser = argparse.ArgumentParser(description="CoFlows Demo program")

    env_addr = os.getenv("COLINK_CORE_ADDR")
    env_jwt = os.getenv("COLINK_JWT")

    parser.add_argument(
        "--addr",
        type=str,
        default=env_addr,
        required=env_addr is None,
        help="CoLink server address.",
    )
    parser.add_argument(
        "--jwt",
        type=str,
        default=env_jwt,
        required=env_jwt is None,
        help="Your JWT issued by the CoLink server.",
    )
    
    parser.add_argument(
        "--include_serve",
        action="store_true",
        help="Include serving the ReverseNumberSequentialFlow"
    )

    args = parser.parse_args()
    return vars(args)

if __name__ == "__main__":
    args = parse_args()
    cl = serve_utils.start_colink_component("Reverse Number Demo", args)
    
    if args["include_serve"]:
       
        # ~~~ Serve ReverseNumberSequential ~~~
        reverse_number_sequential_default_config_path = os.path.join(
            FLOW_MODULES_PATH, "ReverseNumberFlowModule/ReverseNumberSequentialFlow.yaml"
        )
        reverse_number_sequential_default_config = read_yaml_file(
            reverse_number_sequential_default_config_path
        )
        
        
        flow = hydra.utils.instantiate(reverse_number_sequential_default_config, _recursive_=False, _convert_="partial")
        
         # This will serve the flow and all its subflows who have a local user id
        flow.serve(recursive=True)
        #if I want to override with the CL object created here at the start uncomment the line below and comment the line above
        #flow.serve(override_cl=cl, recursive=True)
        
    # ~~~ Mount ReverseNumberSequential --> will recursively mount two ReverseNumberAtomic flows ~~~
    config_overrides = None
    
    flow_ref = serve_utils.recursive_mount(
        cl=cl,
        client_id="local",
        flow_type="ReverseNumberSequentialFlow_served",
        config_overrides=config_overrides,
        initial_state=None,
        dispatch_point_override=None,
    )
    
    colink_overrides = {
        "name": "ReverseNumberSequentialFlow",
        "description": "Proxy flow for ReverseNumberSequentialFlow",
        "user_id": "local",
        "flow_ref": flow_ref,
        "flow_type": "ReverseNumberSequentialFlow_served",
        "colink_info": {
            "cl":{
                "coreaddr": args["addr"],
                "jwt": args["jwt"]
            }
        }
    } 
    
    proxy_flow = AtomicFlow.instantiate_from_default_config(**colink_overrides)
    
   
    print("Pushing to...", flow_ref)

    input_data = {"id": 0, "number": 1234}
    print(proxy_flow.ask(input_data=input_data).get())
    
