

from aiflows.base_flows import CompositeFlow
from aiflows.messages import FlowMessage
from aiflows.interfaces import KeyInterface
class ReverseNumberSequentialFlowNonBlocking(CompositeFlow):
    
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
        
        self.next_state_dict = {
            "first_reverse_flow": "second_reverse_flow",
            "second_reverse_flow": "reply_to_message",
            "reply_to_message": "first_reverse_flow"
        }
    def set_up_flow_state(self):
        super().set_up_flow_state()
        self.flow_state = {"current_state": "first_reverse_flow"}
        
    def get_next_state(self):
        return self.next_state_dict[self.flow_state["current_state"]]
        
    # Customize the logic within this function as needed for your specific Flow requirements.
    def run(self, input_message: FlowMessage):
        
        # Run here is a bit like a switch statement where we decide which flow to call next.
        # We then call the next Flow and pass the input message to it. which we expect to get a reply from 
        # back in the input queue (which will call the run method againg)
        current_state = self.flow_state["current_state"]
        
        # Case where we need to reverse the number for the first time
        if current_state == "first_reverse_flow":
            #Save the initial message to the state
            self.flow_state["initial_message"] = input_message
            
            # Prepares message by editing `reply_data` so that it can get the reply from the first Flow
            # back in the input queue of the composite flow 
            message_for_first_reverse_flow = self.package_input_message(input_message.data)
            # Call the first Flow with non blocking call
            self.subflows["first_reverse_flow"].get_reply(
                message_for_first_reverse_flow
            )
        
        #Case where we need to reverse the number for the second time
        elif current_state == "second_reverse_flow":
            
            # Applies a transformation to the input message (renames keys of dictonary so that they match the
            # required format of the second flow)
            message = self.input_interface_second_reverse_flow(input_message)
            
            # Prepares message by editing `reply_data` so that it can get the reply from the first Flow
            # back in the input queue of the composite flow 
            message_for_second_reverse_flow = self.package_input_message(input_message.data)
            # call the first Flow with non blocking call
            self.subflows["second_reverse_flow"].get_reply(
                message_for_second_reverse_flow
            )
        
        # Case where we need to reply to the initial message (we've already reversed the number twice)
        else:
            message = self.ouput_interface_reply(input_message)
            
            # package ouput message to send back
                # This method packages `response` in a FlowMessage object 
                # containing the necessary metadata to send the message back
                # to the sender of the input message. 
            reply = self.package_output_message(
                input_message = self.flow_state["initial_message"],
                response = message.data
            )
            #send back the reply to initial caller of the Flow
            self.send_message(reply)
            
        self.flow_state["current_state"] = self.get_next_state()
