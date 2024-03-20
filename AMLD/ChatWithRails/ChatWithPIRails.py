
from aiflows.base_flows import CompositeFlow
from aiflows.messages import FlowMessage
from aiflows.interfaces import KeyInterface

class ChatWithPIRails(CompositeFlow):
    
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.input_interface_safeguard = KeyInterface(
            keys_to_rename={"question": "prompt"},
            keys_to_select=["prompt"]
        )
        
        self.input_interface_chatbot = KeyInterface(
            keys_to_select=["question"]
        )
        
    def set_up_flow_state(self):
        super().set_up_flow_state()
        self.flow_state["previous_state"] = None

    def determine_current_state(self):
        previous_state = self.flow_state["previous_state"]
        
        if previous_state is None:
            return "Safeguard"
        
        elif previous_state == "Safeguard":
            if not self.flow_state["is_valid"]:
                return "GenerateReply"
            else:
                return "ChatBot"
            
        elif previous_state == "ChatBot":
            return "GenerateReply"
        
        elif "GenerateReply":
            return None
        
        else:
            raise ValueError(f"Invalid state: {previous_state}")
                        
    def call_chatbot(self):
        
        input_interface = self.input_interface_chatbot
        
        message = self.package_input_message(
            data = input_interface(self.flow_state),
            dst_flow = "ChatBot"
        )
        
        self.subflows["ChatBot"].get_reply(
            message,
            self.get_instance_id(),
        )
        
    def call_safeguard(self):

        input_interface = self.input_interface_safeguard
        
        message = self.package_input_message(
            data = input_interface(self.flow_state),
            dst_flow = "Safeguard"
        )
        
        self.subflows["Safeguard"].get_reply(
                message,
                self.get_instance_id(),
        )
        
    def generate_reply(self):
        
        self.flow_state["previous_state"] = None
        
        reply = self.package_output_message(
            input_message=self.flow_state["initial_message"],
            response={"answer": self.flow_state["answer"]},
        )
        self.send_message(reply)
        
    def register_data_to_state(self, input_message):
        
        previous_state = self.flow_state["previous_state"]
        
        #first call to flow
        if previous_state is None:
            #register initial message so we can reply to it later
            self.flow_state["initial_message"] = input_message
            #register the question
            self.flow_state["question"] = input_message.data["question"]
        
        #case where our last call was to the safeguard
        elif previous_state == "Safeguard":
            self.flow_state["is_valid"] = input_message.data["is_valid"]
            
            if not self.flow_state["is_valid"]:
                self.flow_state["answer"] = "This question is not valid. I cannot answer it."
        
        elif previous_state == "ChatBot":            
            self.flow_state["answer"] = input_message.data["api_output"]
            
    def run(self, input_message: FlowMessage):
        self.register_data_to_state(input_message)
        
        current_state = self.determine_current_state()
        
        if current_state == "Safeguard":
            self.call_safeguard()
            
        elif current_state == "ChatBot":
            self.call_chatbot()
            
        elif current_state == "GenerateReply":
            self.generate_reply()
        
        self.flow_state["previous_state"] = current_state if current_state != "GenerateReply" else None
            
    
