from aiflows.base_flows import CompositeFlow, Flow
from typing import Dict, Any, List
from aiflows.interfaces import KeyInterface
from aiflows.utils import logging
log = logging.get_logger(f"aiflows.{__name__}")


class SamplerFlow(CompositeFlow):
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        self.make_request_for_data = KeyInterface(
            keys_to_set= {"operation": "get_prompt"},
        )
        self.output_interface = KeyInterface(
            keys_to_rename= {"api_output": "artifact"},
            keys_to_select= ["artifact","island_id"]
        )
    
    def run(self, input_data: Dict[str, Any]):
        
        if input_data["retrieved"]:
            
            data = input_data["retrieved"]
            
            output = self.ask_subflow("Sampler", data = data).get_data()
        
            #blocking because I don't want to oveload requests to PDB 
            # and also because it's better when the next sample has more recent programs from the ProgramDB    
            output = self.output_interface({**data,**output})
            
            
            self.tell_subflow("Evaluator", data = output)
        
        else:
            output = {"api_ouput": "No data retrieved from the ProgramDB (No programs available yet)"}
        
        self.ask_pipe_subflow("ProgramDB", data=self.make_request_for_data({}))
        
        
        return output