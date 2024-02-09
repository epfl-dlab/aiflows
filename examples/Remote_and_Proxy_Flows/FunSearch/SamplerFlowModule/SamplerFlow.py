from flow_modules.aiflows.ChatFlowModule import ChatAtomicFlow
from typing import Dict, Any
class SamplerFlow(ChatAtomicFlow):
    def run(self, input_data: Dict[str, Any]):
        breakpoint()
        output = super().run(input_data=input_data)
        output["island_id"] = input_data["island_id"]
        # I just don't feel like dealing with interfaces right now
        output["artifact"] = output["api_output"]
        del output["api_output"]
        breakpoint()
        return output