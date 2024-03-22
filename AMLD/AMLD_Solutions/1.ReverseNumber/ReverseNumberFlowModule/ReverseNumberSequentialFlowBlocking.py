

from aiflows.base_flows import CompositeFlow
from aiflows.messages import FlowMessage
from aiflows.interfaces import KeyInterface
class ReverseNumberSequentialFlowBlocking(CompositeFlow):
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        #~~~~~~~~~~~ Key Transformation solution 1 ~~~~~~~~~~~
        self.input_interface_second_reverse_flow = KeyInterface(
            keys_to_rename= {"reversed_number": "number"},
            keys_to_select= ["number"],
        )
    
        self.ouput_interface_reply = KeyInterface(
            keys_to_rename= {"reversed_number": "output_number"},
            keys_to_select = ["output_number"],
        )
                
    # Customize the logic within this function as needed for your specific flow requirements.
    def run(self, input_message: FlowMessage):
        
        # Call first reverse number
        future_first_reverse = self.subflows["first_reverse_flow"].get_reply_future(
                input_message
            )
        # Get response from first reverse number
        first_reverse_response = future_first_reverse.get_message()
        
        # Prepare response for the second reverse number
        first_reverse_response = self.input_interface_second_reverse_flow(first_reverse_response) 
        
        # Call second reverse number:
        future_second_reverse = self.subflows["second_reverse_flow"].get_reply_future(
            first_reverse_response
        )
        
        second_reverse_response = future_second_reverse.get_data()
        
        # Can call key interface tranformation on both message and dictionaries
        # prepare response for the initial message
        response = self.ouput_interface_reply(second_reverse_response)
        
        reply = self.package_output_message(
            input_message = input_message,
            response = response
        )
        
        self.send_message(
            reply
        )
        
