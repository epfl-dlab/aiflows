
from aiflows.base_flows import AtomicFlow
from aiflows.messages import FlowMessage

class ReverseNumberAtomicFlow(AtomicFlow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    # Customize the logic within this function as needed for your specific flow requirements.
    def run(self, input_message: FlowMessage):

        #Get data dictionary from input message
        input_data = input_message.data
        
        #get input number from data dictionary (int)
        input_number = input_data["number"]
        
        #TODO: reverse the input number (e.g. 1234 -> 4321)
        reversed_number = int(str(input_number)[::-1])
        
        #Create response dictionary
        response = {"reversed_number": reversed_number}
        
        #package ouput message to send back
            #This method packages `response` in a FlowMessage object 
            # containing the necessary metadata to send the message back
            # to the sender of the input message. 
        reply = self.package_output_message(
            input_message=input_message,
            response=response,
        )
        
        #send back reply
        self.send_message(
            reply
        )
