from typing import Dict, Any

from aiflows.base_flows import AtomicFlow

# logging.set_verbosity_debug()  # Uncomment this line to see verbose logs


class ReverseNumberAtomicFlow(AtomicFlow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    # Customize the logic within this function as needed for your specific flow requirements.
    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        print("Called ReverseNumberAtomic")
        input_number = input_data["number"]
        output_number = int(str(input_number)[::-1])
        response = {"output_number": output_number}
        return response
