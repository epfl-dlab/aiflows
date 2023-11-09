from jinja2 import Environment
from typing import List,Dict
class JinjaPrompt:
    def __init__(self,**kwargs):
        self.input_variables: set = set(kwargs.get("input_variables",[]))
        self.partial_variables =  kwargs.get("partial_variables",{})
        self.template: str = kwargs.get("template","")
        self.environment = Environment()
    
    def format(self,**kwargs):
        template = self.environment.from_string(self.template)
        merged_args = {**self.partial_variables,**kwargs}
        return template.render(**merged_args)
    
    def partial(self,**kwargs):
        """Allow to add partials to a prompt"""

        new_partial_variables = {**self.partial_variables,**kwargs}
        new_input_variables = (self.input_variables ^ set(kwargs.keys())) & self.input_variables
        new_jinja_prompt_args = {
           "input_variables": new_input_variables,
           "partial_variables": new_partial_variables,
           "template": self.template
        }
        
        return JinjaPrompt(**new_jinja_prompt_args)
        