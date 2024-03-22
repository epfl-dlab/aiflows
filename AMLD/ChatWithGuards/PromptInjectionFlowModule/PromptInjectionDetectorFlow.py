
from aiflows.base_flows import AtomicFlow
from aiflows.messages import FlowMessage
from llm_guard.input_scanners import PromptInjection
from llm_guard.input_scanners.prompt_injection import MatchType

class PromptInjectionDetectorFlow(AtomicFlow):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.scanner = PromptInjection(threshold=self.flow_config["threshold"], match_type=MatchType.FULL)
        
    def run(self, input_message: FlowMessage):
        
        input_data = input_message.data

        prompt = input_data["prompt"] 
        
        _, is_valid, _ = self.scanner.scan(prompt)
        
        reply = self.package_output_message(
            input_message=input_message,
            response={"is_valid": is_valid},
        )
        
        self.send_message(reply)
        
