from typing import Dict, Any

from aiflows.base_flows import CompositeFlow
from aiflows.interfaces.key_interface import KeyInterface
# logging.set_verbosity_debug()  # Uncomment this line to see verbose logs
import aiflows.data_transformations as kt

class ReverseNumberSequentialFlow(CompositeFlow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        #~~~~~~~~~~~ Key Transformation solution 1 ~~~~~~~~~~~
        self.transformation_1 = KeyInterface(
            keys_to_rename= {"output_number": "number"},
            keys_to_select= ["number"],
        )
    
        self.transformation_2 = KeyInterface(
            keys_to_select = ["output_number"],
        )
        
        #~~~~~~~~~~~ Key Transformation solution 2 ~~~~~~~~~~~
        # self.rename_output = kt.KeyRename({"output_number": "number"})
        # self.select_number = kt.KeySelect(["number"])   
        # self.select_output_number = kt.KeySelect(["output_number"]) 

    # Customize the logic within this function as needed for your specific flow requirements.
    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        print("Called ReverseNumberSequential", "\n", "state", self.flow_state)
        
        future1 = self.ask_subflow("first_reverse_flow", data=input_data)
        output1 = future1.get_data()# blocking
        
        
        # ~~~~~~~~~~~ Key Transformation solution 1 ~~~~~~~~~~~
        output1 = self.transformation_1(output1)
        # # ~~~~~~~~~~~ Key Transformation solution 2 ~~~~~~~~~~~
        # output1 = self.select_number(self.rename_output(output1))
        
        future2 = self.ask_subflow("second_reverse_flow", data=output1)
        output2 = future2.get_data()  # blocking
        
        # ~~~~~~~~~~~ Key Transformation solution 1 ~~~~~~~~~~~
        response = self.transformation_2(output2)
        # # ~~~~~~~~~~~ Key Transformation solution 2 ~~~~~~~~~~~
        # response = self.select_output_number(output2)
        return response
