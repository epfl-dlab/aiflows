from typing import Dict, Any

from aiflows.base_flows import CompositeFlow
from aiflows.interfaces.key_interface import KeyInterface
# logging.set_verbosity_debug()  # Uncomment this line to see verbose logs
import aiflows.data_transformations as kt
from aiflows.messages import FlowMessage

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
        
        
        
        #~~~~~~~~~~~ Key Transformation solution 2 ~~~~~~~~~~~
        # self.rename_output = kt.KeyRename({"output_number": "number"})
        # self.select_number = kt.KeySelect(["number"])   
        # self.select_output_number = kt.KeySelect(["output_number"]) 
    
    def set_up_flow_state(self):
        super().set_up_flow_state()
        self.flow_state = {"current_call": "first_reverse_flow"}
        
    
    # Customize the logic within this function as needed for your specific flow requirements.
    def run(self, input_message):
        
        ############### OPTION 1 (blocking calls) #####################
        # print("Called ReverseNumberSequential", "\n", "state", self.flow_state)
        
        # future1 = self.subflows["first_reverse_flow"].ask(input_message)
        # output1 = future1.get_message()# blocking
        
        
        # # ~~~~~~~~~~~ Key Transformation solution 1 ~~~~~~~~~~~
        # output1 = self.transformation_1(output1)
        # # # ~~~~~~~~~~~ Key Transformation solution 2 ~~~~~~~~~~~
        # # output1 = self.select_number(self.rename_output(output1))
                
        # future2 = self.subflows["second_reverse_flow"].ask(output1)
        # output2 = future2.get_message()  # blocking
        
        # # ~~~~~~~~~~~ Key Transformation solution 1 ~~~~~~~~~~~
        # response = self.transformation_2(output2)
        # # # ~~~~~~~~~~~ Key Transformation solution 2 ~~~~~~~~~~~
        # # response = self.select_output_number(output2)
        # self.reply(message = response,to =input_message)
        
        
        ################# OPTION 2 (non-blocking calls) #####################
        
        print("Called ReverseNumberSequential", "\n", "state", self.flow_state)
        
        curr_call = self.flow_state["current_call"]
        
        if curr_call == "first_reverse_flow":
            self.flow_state["initial_message"] = input_message
            self.subflows["first_reverse_flow"].ask_pipe(
                input_message,
                parent_flow_ref=self.flow_config["flow_ref"]
            )
            
        elif curr_call == "second_reverse_flow":
            
            message = self.transformation_1(input_message) 
            
            self.subflows["first_reverse_flow"].ask_pipe(
                message,
                parent_flow_ref=self.flow_config["flow_ref"]
            )
            
        else:
            message = self.transformation_2(input_message)
            self.reply(message=message, to=self.flow_state["initial_message"])
        
        self.flow_state["current_call"] = self.get_next_call[curr_call]
      
