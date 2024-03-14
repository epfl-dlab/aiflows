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
                
        self.forward_to_evaluator = KeyInterface(
            keys_to_set={"forward_to": "EvaluatorFlow"},
        )
        
        self.output_interface = KeyInterface(
            keys_to_rename= {"api_output": "artifact"},
            keys_to_select= ["artifact","island_id"]
        )
    
    def run(self, input_data: Dict[str, Any]):
        
        if input_data["retrieved"]:
            
            data = input_data["retrieved"]
            
            #blocking because I don't want to oveload requests to PDB 
            # and also because it's better when the next sample has more recent programs from the ProgramDB 
            output = self.ask_subflow("Sampler", data = data).get_data()
                    
        
            output = self.forward_to_evaluator(self.output_interface({**data,**output}))
            
        else:
            #If no data is retrieved, then we crea
            output = self.output_interface({"api_output": None, "island_id": None})
        
        self.ask_pipe_subflow("ProgramDB", data=self.make_request_for_data({}))
        breakpoint()
        return output