from typing import Dict, Any

from flow_modules.aiflows.ControllerExecutorFlowModule import ControllerExecutorFlow
from aiflows.interfaces import KeyInterface

class ReActWithHumanFeedback(ControllerExecutorFlow):
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.human_output_interface = KeyInterface(
            keys_to_rename={"human_input": "human_feedback"}
        )
        self.input_interface_loop = KeyInterface(
            keys_to_select=["goal", "observation", "human_feedback"]
        )
    
    def _single_round_ctrl_ex_human_feedback(self,in_data):
        
        #first round observation and humand feedback are None
        in_data["executor_reply"]["goal"] = self.flow_state["goal"]
                
        reply = self._single_round_controller_executor(in_data)
        
        if reply.get("EARLY_EXIT",False):
            return reply
        
        controller_reply = reply["controller_reply"]
        executor_reply = reply["executor_reply"]
        
        human_feedback_input_variables = {
            "goal": self.flow_state["goal"],
            "command": controller_reply["command"],
            "command_args": controller_reply["command_args"],
            "observation": executor_reply,
        }
        
        human_feedback = self.human_output_interface(self.ask_subflow("HumanFeedback",human_feedback_input_variables).get_data())
        
        if human_feedback["human_feedback"].strip().lower() == "q":
            return {
                "EARLY_EXIT": True,
                "answer": "The user has chosen to exit before a final answer was generated.",
                "status": "unfinished",
            }

        reply["executor_reply"]["human_feedback"] = human_feedback["human_feedback"]
        
        return reply
    
    def run(self,input_data):
    
        reply = {
            "executor_reply": input_data,
        }
        
        self._state_update_dict({"goal": input_data["goal"]})
         
        for round in range(self.flow_config["max_rounds"]):
            
            reply = self._single_round_ctrl_ex_human_feedback(reply)
            
            if reply.get("EARLY_EXIT",False):
                return reply

                
        self._on_reach_max_rounds()
        
        return {
            "EARLY_EXIT": False,
            "answer": reply["executor_reply"]["observation"],
            "status": "unfinished"
        }
        
    