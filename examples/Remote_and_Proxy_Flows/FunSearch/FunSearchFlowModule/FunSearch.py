
from aiflows.base_flows import BranchingFlow
from aiflows.utils import logging
from aiflows.utils.colink_helpers import get_next_update_message
import pickle
log = logging.get_logger(f"aiflows.{__name__}")

class FunSearch(BranchingFlow):
    
    def _get_name_of_subflow_to_call(self,input_data):
                
        if "scores_per_test" in input_data or "get_prompt"  in input_data:
            return "ProgramDBFlow"
        
        elif "retrieved" in input_data:
            if input_data["retrieved"] == "":
                return "do_nothing"
            return "SamplerFlow"
        
        # else: # input_data == "api_output"
        return "EvaluatorFlow"

    
    def run(self,input_data):
        breakpoint()
        branch = self._get_name_of_subflow_to_call(input_data)
        if branch == "do_nothing":
            return {"message_sent_confirmation": "do_nothing"}
        breakpoint()
        data = {"branch": branch, "branch_input_data": input_data}
        
        message_sent_confirmation = super().run(data)
        
        return message_sent_confirmation
    
    
  