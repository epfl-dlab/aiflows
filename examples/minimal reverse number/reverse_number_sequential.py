import os

import hydra

import aiflows
from aiflows.backends.api_info import ApiInfo
from aiflows.utils.general_helpers import read_yaml_file, quick_load_api_keys

from aiflows import logging
from aiflows.flow_cache import CACHING_PARAMETERS, clear_cache

from aiflows.utils import serve_utils
from aiflows.workers import run_dispatch_worker_thread
from aiflows.messages import FlowMessage
from aiflows.interfaces import KeyInterface
from aiflows.utils.colink_utils import start_colink_server
from aiflows.workers import run_dispatch_worker_thread
from aiflows.base_flows import CompositeFlow
# logging.set_verbosity_debug()  # Uncomment this line to see verbose logs

class ReverseNumberSequentialFlow(CompositeFlow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        #~~~~~~~~~~~ Key Transformation solution 1 ~~~~~~~~~~~
        self.transformation_1 = KeyInterface(
            keys_to_rename= {"output_number": "number"},
            keys_to_select= ["number"],
        )
    
        self.transformation_2 = KeyInterface(
            keys_to_select = ["output_number"],
        )
        
        self.get_next_call = {
            "first_reverse_flow": "second_reverse_flow",
            "second_reverse_flow": "reply_to_message",
            "reply_to_message": "first_reverse_flow"
        }
        
    
    def set_up_flow_state(self):
        super().set_up_flow_state()
        self.flow_state = {"current_call": "first_reverse_flow"}
        
    # Customize the logic within this function as needed for your specific flow requirements.
    def run(self, input_message):
                        
        curr_call = self.flow_state["current_call"]
        
        if curr_call == "first_reverse_flow":
            self.flow_state["initial_message"] = input_message
            self.subflows["first_reverse_flow"].get_reply(
                input_message,
                self.get_instance_id()
            )
            
        elif curr_call == "second_reverse_flow":
            
            message = self.transformation_1(input_message) 
            
            self.subflows["first_reverse_flow"].get_reply(
                message,
                self.get_instance_id()
            )
            
        else:
            message = self.transformation_2(input_message)
            
            reply = self.package_output_message(self.flow_state["initial_message"], message)
            
            self.send_message(reply, is_reply = True)
        
        self.flow_state["current_call"] = self.get_next_call[curr_call]

if __name__ == "__main__":
    
    #1. ~~~~~ Set up a colink server ~~~~
    FLOW_MODULES_PATH = "./"
    
    cl = start_colink_server()


    #2. ~~~~~Load flow config~~~~~~
    root_dir = "."
    cfg_path = os.path.join(root_dir, "reverseNumberSequential.yaml")
    cfg = read_yaml_file(cfg_path)
    
    #2.1 ~~~ Set the API information ~~~
    # OpenAI backend
    api_information = [ApiInfo(backend_used="openai",
                              api_key = os.getenv("OPENAI_API_KEY"))]
    # # Azure backend
    # api_information = ApiInfo(backend_used = "azure",
    #                           api_base = os.getenv("AZURE_API_BASE"),
    #                           api_key = os.getenv("AZURE_OPENAI_KEY"),
    #                           api_version =  os.getenv("AZURE_API_VERSION") )
    
    
    quick_load_api_keys(cfg, api_information, key="api_infos")

    
    #3. ~~~~ Serve The Flow ~~~~
    serve_utils.recursive_serve_flow(
        cl = cl,
        flow_type="reverseNumberSequential",
        default_config=cfg,
        default_state=None,
        default_dispatch_point="coflows_dispatch"
    )
    
    #4. ~~~~~Start A Worker Thread~~~~~
    run_dispatch_worker_thread(cl, dispatch_point="coflows_dispatch", flow_modules_base_path=FLOW_MODULES_PATH)

    #5. ~~~~~Mount the flow and get its proxy~~~~~~
    proxy_flow = serve_utils.recursive_mount(
        cl=cl,
        client_id="local",
        flow_type="reverseNumberSequential",
        config_overrides=None,
        initial_state=None,
        dispatch_point_override=None,
    )   
    
    #6. ~~~ Get the data ~~~
    data = {"id": 0, "number": 1234}
   
    
    #option1: use the FlowMessage class
    input_message = FlowMessage(
        data=data,
    )

    #option2: use the proxy_flow
    #input_message = proxy_flow.package_input_message(data = data)
    
    #7. ~~~ Run inference ~~~
    future = proxy_flow.get_reply_future(input_message)
    
    #uncomment this line if you would like to get the full message back
    #reply_message = future.get_message()
    reply_data = future.get_data()
    
    # ~~~ Print the output ~~~
    print("~~~~~~Reply~~~~~~")
    print(reply_data)
    
    
    #8. ~~~~ (Optional) apply output interface on reply ~~~~
    # output_interface = KeyInterface(
    #     keys_to_rename={"api_output": "answer"},
    # )
    # print("Output: ", output_interface(reply_data))
    
    
    #9. ~~~~~Optional: Unserve Flow~~~~~~
    # serve_utils.delete_served_flow(cl, "FlowModule")
