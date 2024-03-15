import numpy as np
from .artifacts import AbstractArtifact
from .utils import _softmax
class Cluster:
    def __init__(self,score: float,first_program: AbstractArtifact,epsilon=1e-6,sample_with_replacement=False, default_program_temperature=0.1):
        self.score: float = score
        self.programs: list[AbstractArtifact] = [first_program]
        self.lengths = np.array([len(str(first_program))],dtype=np.float32)
        self.epsilon = epsilon
        self.sample_with_replacement = sample_with_replacement
        self.default_program_temperature = default_program_temperature
        
        
    def compute_length_probs(self,program_temperature: float):
        min_length = np.min(self.lengths)
        max_length = np.max(self.lengths)
        

        length_logits = (self.lengths - min_length)/(max_length  + self.epsilon)
        
        probs =  _softmax(-length_logits,program_temperature)
        return probs
    
    def register_program(self,program: str):
        self.programs.append(program)
        self.lengths = np.append(self.lengths,len(str(program)))
        
    def sample_program(self,program_temperature=None):
        
        if program_temperature is None:
            program_temperature = self.default_program_temperature
        
        
        probs = self.compute_length_probs(program_temperature)
        #sample an index of probs randomly givent the probs
        index = np.random.choice(len(probs),p=probs,replace=self.sample_with_replacement)
        
        return self.programs[index]