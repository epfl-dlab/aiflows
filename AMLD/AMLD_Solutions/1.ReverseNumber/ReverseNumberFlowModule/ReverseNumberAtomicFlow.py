

from aiflows.base_flows import AtomicFlow
from aiflows.messages import FlowMessage

class ReverseNumberAtomicFlow(AtomicFlow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    # Customize the logic within this function as needed for your specific Flow requirements.
    def run(self, input_message: FlowMessage):
        ## ~~~~ Getting the input ~~~~

        # Get the input dictionary from the input message
        input_data = input_message.data
        
        # Get input number from data dictionary
        input_number = input_data["number"]
        
        ## ~~~~ Main logic ~~~~
        ########## YOUR CODE GOES HERE ##########
        # TODO: Reverse the input number (e.g. 1234 -> 4321)
        reversed_number = int(str(input_number)[::-1])
        ########## YOUR CODE GOES HERE ##########
        
        # ~~~ Preparing the response message ~~~
        response = {"reversed_number": reversed_number}
        
        # This method packages the `response` in a FlowMessage object 
        # containing the necessary metadata to send the message back
        # to the sender of the input message  
        reply = self.package_output_message(
            input_message=input_message,
            response=response,
        )
        
        # ~~~ Sending the response ~~~
        self.send_message(
            reply
        )

