from typing import Dict, Any

from aiflows.base_flows import CompositeFlow

# logging.set_verbosity_debug()  # Uncomment this line to see verbose logs


class ReverseNumberSequentialFlow(CompositeFlow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    # Customize the logic within this function as needed for your specific flow requirements.
    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        print("Called ReverseNumberSequential", "\n", "state", self.flow_state)

        future1 = self.ask_subflow("first_reverse_flow", data=input_data)
        output1 = future1.get(output_data_only=True)# blocking
        
        future2 = self.ask_subflow("second_reverse_flow", data={ "number": output1["output_number"]})
        output2 = future2.get(output_data_only=True)  # blocking
        
        response = {"output_number": output2["output_number"]}
        return response
