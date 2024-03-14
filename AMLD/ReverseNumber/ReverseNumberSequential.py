

from aiflows.base_flows import CompositeFlow
from aiflows.messages import FlowMessage
from aiflows.interfaces import KeyInterface
class ReverseNumberSequentialFlow(CompositeFlow):
    
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
        
        self.get_next_call = {
            "first_reverse_flow": "second_reverse_flow",
            "second_reverse_flow": "reply_to_message",
            "reply_to_message": "first_reverse_flow"
        }
    def set_up_flow_state(self):
        super().set_up_flow_state()
        self.flow_state = {"flow_to_call": "first_reverse_flow"}
        
    def get_next_flow_to_call(self):
        return self.get_next_call[self.flow_state["flow_to_call"]]
        
    # Customize the logic within this function as needed for your specific flow requirements.
    def run(self, input_message: FlowMessage):
        
        #Run here is a bit like a switch statement where we decide which flow to call next.
        # We then call the next flow and pass the input message to it. which we expect to get a reply from 
        # back in the input queue (which will call the run method againg)
        flow_to_call = self.flow_state["flow_to_call"]
        
        #Case where we need to reverse the number for the first time
        if flow_to_call == "first_reverse_flow":
            #Save the initial message to the state
            self.flow_state["initial_message"] = input_message
            
            #Calls the first flow and requests a reply to be sent back to the input queue 
            # (The queue to send back to is specified by self.get_instance_id() --> id of this flow instance
            # of ReverseNumberSequentialFlow)
            self.subflows["first_reverse_flow"].get_reply(
                input_message,
                self.get_instance_id()
            )
        
        #Case where we need to reverse the number for the second time
        elif flow_to_call == "second_reverse_flow":
            
            #Applies a transformation to the input message (renames keys of dictonary so that they match the
            # required format of the second flow)
            message = self.input_interface_second_reverse_flow(input_message)
            
            #TODO: Call the second flow and requests a reply to be sent back to the input queue
            self.subflows["second_reverse_flow"].get_reply(
                input_message,
                self.get_instance_id()
            )
        
        #Case where we need to reply to the initial message (we've already reversed the number twice)
        else:
            message = self.ouput_interface_reply(input_message)
            
            #package ouput message to send back
                #This method packages `response` in a FlowMessage object 
                # containing the necessary metadata to send the message back
                # to the sender of the input message. 
            reply = self.package_output_message(
                input_message = self.flow_state["initial_message"],
                response = message.data
            )
            #send back the reply to initial caller of the flow
            self.send_message(reply, is_reply = True)
            
        self.flow_state["flow_to_call"] = self.get_next_flow_to_call()
