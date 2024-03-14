
from aiflows.base_flows import AtomicFlow
from .Island import Island,ScoresPerTest
import numpy as np
from typing import Callable,Dict,Union, Any,Optional, List
import time
from aiflows.utils import logging
from .artifacts import AbstractArtifact
from .Program import Program,text_to_artifact
import ast
import os

log = logging.get_logger(f"aiflows.{__name__}")

class ProgramDBFlow(AtomicFlow):
    def __init__(self,
                 **kwargs
                ):
        super().__init__(**kwargs)
        
        #Unpack config (for clarity)
        self.artifact_to_evolve_name: str = self.flow_config["artifact_to_evolve_name"]
        
        self.artifacts_per_prompt: int = self.flow_config["artifacts_per_prompt"]
        self.temperature: float = self.flow_config["temperature"]
        self.temperature_period: int = self.flow_config["temperature_period"]
        self.reduce_score_method: Callable = np.mean 
        self.sample_with_replacement: bool = self.flow_config["sample_with_replacement"]
        self.num_islands: int = self.flow_config["num_islands"]
        self.portion_of_islands_to_reset: float = self.flow_config["portion_of_islands_to_reset"]
        self.reset_period: float = self.flow_config["reset_period"]
        
        self.evaluate_function = self.flow_config["evaluate_function"]
        self.evaluate_file_full_content = self.flow_config["evaluate_file_full_content"] 
        
        
        
        assert self.portion_of_islands_to_reset <= 1.0 and self.portion_of_islands_to_reset >= 0.0, "portion_of_islands_to_reset must be between 0 and 1"
        
        self.islands_to_reset = int(round(self.portion_of_islands_to_reset * self.num_islands)) #round to nearest integer
        
          
    def set_up_flow_state(self):
        """ This method sets up the state of the flow and clears the previous messages."""
        super().set_up_flow_state()
        
        preface = \
            self.flow_config["template"]["preface"] + "\n\n" "#function used to evaluate the program:\n" + self.flow_config["evaluate_function"] + "\n\n"
            
        self.template: Program = Program(preface =preface,artifacts = [])
        
        # ~~~instantiate isladns~~~
        self.flow_state["islands"] = [
            Island(
                artifact_to_evolve_name =self.flow_config["artifact_to_evolve_name"],
                artifacts_per_prompt = self.flow_config["artifacts_per_prompt"],
                temperature = self.flow_config["temperature"],
                temperature_period = self.flow_config["temperature_period"],
                reduce_score_method = np.mean,
                sample_with_replacement = self.flow_config["sample_with_replacement"],
                template=self.template
                )
        for _ in range(self.flow_config["num_islands"])
        ]
        
        self.flow_state["last_reset_time"] = time.time()
        self.flow_state["best_score_per_island"] = [float("-inf") for _ in range(self.flow_config["num_islands"])]
        self.flow_state["best_program_per_island"] = [None for _ in range(self.flow_config["num_islands"])]
        self.flow_state["best_scores_per_test_per_island"] = [None for _ in range(self.flow_config["num_islands"])]
        self.flow_state["first_program_registered"] = False
          
    def get_prompt(self):
        island_id = np.random.choice(len(self.flow_state["islands"]))
        code, version_generated = self.flow_state["islands"][island_id].get_prompt()
        return code,version_generated,island_id
    
    def reset_islands(self):
        # gaussian noise to break ties
        sorted_island_ids = np.argsort(
            np.array(self.flow_state["best_score_per_island"]) +
            (np.random.randn(len(self.flow_state["best_score_per_island"])) * 1e-6)
        )
        
        reset_island_ids = sorted_island_ids[:self.islands_to_reset]
        keep_island_ids = sorted_island_ids[self.islands_to_reset:]
       
        for island_id in reset_island_ids:
            self.flow_state["islands"][island_id] = Island(
                               artifact_to_evolve_name =self.artifact_to_evolve_name,
                               artifacts_per_prompt = self.artifacts_per_prompt,
                               temperature = self.temperature,
                               temperature_period = self.temperature_period,
                               reduce_score_method = np.mean,
                               sample_with_replacement = self.sample_with_replacement,
                               template=self.template
                               )
            
            self.flow_state["best_score_per_island"][island_id] = float("-inf")
            founder_island_id = np.random.choice(keep_island_ids)
            founder = self.flow_state["best_score_per_island"][founder_island_id]
            founder_scores = self.flow_state["best_scores_per_test_per_island"][founder_island_id]
            self._register_program_in_island(program=founder,island_id=island_id,scores_per_test=founder_scores)
        
    
    
    def register_program(self, program: AbstractArtifact ,island_id: int,scores_per_test: ScoresPerTest):
        if not program.calls_ancestor(artifact_to_evolve=self.artifact_to_evolve_name):
            #program added at the beggining, so add to all islands
            if island_id is None:
                for id in range(self.num_islands):
                    self._register_program_in_island(program=program,island_id=id,scores_per_test=scores_per_test)
                    
            else:
                self._register_program_in_island(program=program,island_id=island_id,scores_per_test=scores_per_test)
            
        #reset islands if needed
        if time.time() - self.flow_state["last_reset_time"]> self.reset_period:
            self.reset_islands()
            self.flow_state["last_reset_time"] = time.time()
    
    def _register_program_in_island(self,program: AbstractArtifact, scores_per_test: ScoresPerTest, island_id: Optional[int] = None):
        self.flow_state["islands"][island_id].register_program(program,scores_per_test)
        
        scores_per_test_values = np.array([ score_per_test["score"] for score_per_test in scores_per_test.values()])
        score = self.reduce_score_method(scores_per_test_values)
        
        if score > self.flow_state["best_score_per_island"][island_id]:
            self.flow_state["best_score_per_island"][island_id] = score
            self.flow_state["best_program_per_island"][island_id] = str(program)
            self.flow_state["best_scores_per_test_per_island"][island_id] = scores_per_test
    
    def get_best_programs(self) -> List[Dict[str,Any]]:
        sorted_island_ids = np.argsort(np.array(self.flow_state["best_score_per_island"]))
        return {
        "best_island_programs": [
            {
                "rank": rank,
                "score": self.flow_state["best_score_per_island"][island_id],
                "program": self.flow_state["best_program_per_island"][island_id]
                }
            for rank,island_id in enumerate(sorted_island_ids)
            ]
        }
    

    def run(self,input_data: Dict[str,any]):
        
        operation = input_data["operation"]
        
        possible_operations = [
            "register_program",
            "get_prompt",
            "get_best_programs_per_island",
        ]
        
        if operation not in possible_operations:
            raise ValueError(f"operation must be one of the following: {possible_operations}")
        response = {}
        if operation == "get_prompt":
            response["retrieved"] = False
            
            if not self.flow_state["first_program_registered"]:
                response["retrieved"] = False
            
            else:
                code,version_generated,island_id = self.get_prompt()
                
                response["retrieved"] = {
                    "code":code,
                    "version_generated": version_generated,
                    "island_id":island_id,
                    "header": self.evaluate_file_full_content
                }
            
        elif operation == "register_program":
            
            try:
                artifact = text_to_artifact(input_data["artifact"])
                island_id = input_data.get("island_id",None)
                scores_per_test = input_data.get("scores_per_test",None)
                if scores_per_test is not None:
                    self.register_program(program=artifact,island_id=island_id,scores_per_test=scores_per_test)
                response["retrieved"] = "Program registered"
                self.flow_state["first_program_registered"] = True
            except:
                response["retrieved"] = "Program failed to register"
        else:
            response["retrieved"] = self.get_best_programs()
        breakpoint()
        return response