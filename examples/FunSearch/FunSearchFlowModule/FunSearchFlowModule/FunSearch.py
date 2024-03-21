from aiflows.base_flows import CompositeFlow
from aiflows.utils import logging
log = logging.get_logger(f"aiflows.{__name__}")
class FunSearch(CompositeFlow):
        
    def run(self,input_data):
        
        forward_to = input_data.pop("forward_to", None)
        
        if forward_to is not None:
            
            if "operation" in input_data and input_data["operation"] == "get_best_programs_per_island":
                future = self.ask_subflow(forward_to, input_data)
                output = {"reply": future.get_data()}
                
            else:
                self.ask_pipe_subflow(forward_to, input_data)
                output = {"reply": "Message forwarded to " + forward_to}
        
        else:
            output = {"reply": "Message not forwarded because no forward_to key was found in input_data"}        
        breakpoint()
        return output
    