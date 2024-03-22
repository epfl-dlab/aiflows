
from aiflows.base_flows import CompositeFlow
from aiflows.messages import FlowMessage
from aiflows.interfaces import KeyInterface

class ChatWithPIGuard(CompositeFlow):
    
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        
        #Define the input interface for the safeguard
        self.input_interface_safeguard = KeyInterface(
            keys_to_rename={"question": "prompt"},
            keys_to_select=["prompt"]
        )
        
        #Define the input interface for the chatbot
        self.input_interface_chatbot = KeyInterface(
            keys_to_select=["question"]
        )
        
    def set_up_flow_state(self):
        """ Sets up the flow state (called in super().__init__()"""
        super().set_up_flow_state()
        self.flow_state["previous_state"] = None

    def determine_current_state(self):
        """ Given the current state, determines the next state of the flow (next action to do)"""
        previous_state = self.flow_state["previous_state"]
        
        #If this is the first call to the flow
        if previous_state is None:
            # return the safeguard (prompt injection detector)
            return "Safeguard"
        
        #if the previous state was the safeguard
        elif previous_state == "Safeguard":
            #if the question is not valid, we don't need to call the chatbot
            if not self.flow_state["is_valid"]:
                return "GenerateReply"
            else:
                return "ChatBot"
        
        #if the previous state was the chatbot
        elif previous_state == "ChatBot":
            #generate the reply
            return "GenerateReply"
        #if the previous state was the generate reply, we are done
        elif "GenerateReply":
            return None
        
        else:
            raise ValueError(f"Invalid state: {previous_state}")
                        
    def call_chatbot(self):
        """ Calls the chatbot flow (non-blocking)"""
        input_interface = self.input_interface_chatbot
        
        message = self.package_input_message(
            data = input_interface(self.flow_state),
            dst_flow = "ChatBot"
        )
        
        self.subflows["ChatBot"].get_reply(
            message,
        )
        
    def call_safeguard(self):
        """ Calls the safeguard flow (non-blocking)"""
        input_interface = self.input_interface_safeguard
        
        message = self.package_input_message(
            data = input_interface(self.flow_state),
            dst_flow = "Safeguard"
        )
        
        self.subflows["Safeguard"].get_reply(
                message,
        )
        
    def generate_reply(self):
        """ Replies back to the initial message with the answer"""
        
        reply = self.package_output_message(
            input_message=self.flow_state["initial_message"],
            response={"answer": self.flow_state["answer"]},
        )
        self.send_message(reply)
        
    def register_data_to_state(self, input_message):
        """ Registers the data from the input message to the flow state"""
        previous_state = self.flow_state["previous_state"]
        
        #first call to flow
        if previous_state is None:
            #register initial message so we can reply to it later
            self.flow_state["initial_message"] = input_message
            #register the question
            self.flow_state["question"] = input_message.data["question"]
        
        #case where our last call was to the safeguard
        elif previous_state == "Safeguard":
            #register the result of the safeguard
            self.flow_state["is_valid"] = input_message.data["is_valid"]
            #if the question is not valid, we don't need to call the chatbot and can generate the default answer
            if not self.flow_state["is_valid"]:
                self.flow_state["answer"] = "This question is not valid. I cannot answer it."
        
        #case where our last call was to the chatbot
        elif previous_state == "ChatBot":           
            #register the answer from the chatbot 
            self.flow_state["answer"] = input_message.data["api_output"]
            
    def run(self, input_message: FlowMessage):
        #register the data from the input message to the flow state
        self.register_data_to_state(input_message)
        
        #determine the next state (next action to do)
        current_state = self.determine_current_state()
        
        ## Sort of like a state machine
        if current_state == "Safeguard":
            self.call_safeguard()
            
        elif current_state == "ChatBot":
            self.call_chatbot()
            
        elif current_state == "GenerateReply":
            self.generate_reply()
        #update the previous state
        self.flow_state["previous_state"] = current_state if current_state != "GenerateReply" else None
            
    
