from typing import Dict, Any

from aiflows.base_flows import CompositeFlow

# logging.set_verbosity_debug()  # Uncomment this line to see verbose logs


class ReverseNumberSequentialFlow(CompositeFlow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    # Customize the logic within this function as needed for your specific flow requirements.
    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        print("Called ReverseNumberSequential")
        future1 = self.subflows["first_reverse_flow"].ask(input_data)
        output1 = future1.get()  # blocking

        next_dict = {"id": 0, "number": output1["data_dict"]["output_number"]}
        future2 = self.subflows["second_reverse_flow"].ask(next_dict)
        output2 = future2.get()  # blocking

        response = {"output_number": output2["data_dict"]["output_number"]}
        return response
