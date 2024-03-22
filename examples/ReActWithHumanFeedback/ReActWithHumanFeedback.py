from typing import Dict, Any

from flow_modules.aiflows.ControllerExecutorFlowModule import ControllerExecutorFlow
from aiflows.interfaces import KeyInterface

class ReActWithHumanFeedback(ControllerExecutorFlow):
    
    def __init__(self, **kwargs):
        super().__init__( **kwargs)
        self.rename_human_output_interface = KeyInterface(
            keys_to_rename={"human_input": "human_feedback"}
        )
        
        self.input_interface_controller = KeyInterface(
            keys_to_select = ["goal","observation","human_feedback"],
        )
        
        self.input_interface_human_feedback = KeyInterface(
            keys_to_select = ["goal","command","command_args","observation"],
        )
        
        self.human_feedback_ouput_interface = KeyInterface(
            keys_to_rename={"human_input": "human_feedback"},
            keys_to_select = ["human_feedback"],
        )
            
        self.next_state = {
            None: "Controller",
            "Controller": "Executor",
            "Executor": "HumanFeedback",
            "HumanFeedback": "Controller",
        }
            
    def set_up_flow_state(self):
        super().set_up_flow_state()
        self.flow_state["early_exit_flag"] = False
        

    def call_human_feedback(self):
            
        message = self.package_input_message(
            data = self.input_interface_human_feedback(self.flow_state),
            dst_flow = "HumanFeedback",
        )
        
        self.subflows["HumanFeedback"].get_reply(
            message,
        )
             
    def register_data_to_state(self, input_message):
        
        #Making this explicit so it's easier to understand
        #I'm also showing different ways of writing to the state
        # either programmatically or using the _state_update_dict and 
        # input and ouput interface methods
        
        last_state = self.flow_state["last_state"]
        
        if last_state is None:            
            self.flow_state["input_message"] = input_message
            self.flow_state["goal"] = input_message.data["goal"]
        
        elif last_state == "Executor":
            self.flow_state["observation"] = input_message.data
        
        elif last_state == "Controller":
            self._state_update_dict(
                {
                    "command": input_message.data["command"],
                    "command_args": input_message.data["command_args"]
                }
            )
            
            #detect and early exit
            if self.flow_state["command"] == "finish":
                
                self._state_update_dict(
                    {
                        "EARLY_EXIT": True,
                        "answer": self.flow_state["command_args"]["answer"],
                        "status": "finished"
                    }
                )
                self.flow_state["early_exit_flag"] = True
                
            
        elif last_state == "HumanFeedback":
            self._state_update_dict(
                self.human_feedback_ouput_interface(input_message).data
            )
            
            #detect early exit
            if self.flow_state["human_feedback"].strip().lower() == "q":
                
                self._state_update_dict(
                    {
                        "EARLY_EXIT": True,
                        "answer": "The user has chosen to exit before a final answer was generated.",
                        "status": "unfinished",
                    }
                )
                
                self.flow_state["early_exit_flag"] = True
        
    def run(self,input_message):
        
        self.register_data_to_state(input_message)
        
        current_state = self.get_next_state()

        if self.flow_state.get("early_exit_flag",False):
            self.generate_reply()
            
        elif current_state == "Controller":
            self.call_controller()
        
        elif current_state == "Executor":
            self.call_executor()
        
        elif current_state == "HumanFeedback":
            self.call_human_feedback()
            self.flow_state["current_round"] += 1
            
        else:
            self._on_reach_max_round()
            self.generate_reply()
            
        if self.flow_state.get("early_exit_flag",False) or current_state is None:
            self.flow_state["last_state"] = None
        else:
            self.flow_state["last_state"] = current_state
        
    