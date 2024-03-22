
from aiflows.base_flows import CompositeFlow
from aiflows.messages import FlowMessage
from aiflows.interfaces import KeyInterface

class ChatCodeInterpreter(CompositeFlow):
        
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        # Input to generate reply
        self.input_interface_generate_reply = KeyInterface(
            keys_to_rename={"question": "prompt"},
            keys_to_select=["code", "interpreter_output"]
        )
        
        # Input to call the coder
        self.first_input_interface_coder = KeyInterface(
            keys_to_select=["goal"]
        )
        
        # Input to call the interpreter
        self.input_interface_coder = KeyInterface(
            keys_to_rename={"code": "previous_code", "interpreter_output": "feedback"},
            keys_to_select=["goal", "previous_code", "feedback"]
        )
        
        # Input to call the interpreter
        self.input_interface_interpreter = KeyInterface(
            keys_to_rename={"code": "code", "language_of_code": "language"},
            keys_to_select=["code", "language"]
        )
        
    def set_up_flow_state(self):
        """ Set up the flow state. (called in __init__)"""
        super().set_up_flow_state()
        self.flow_state["previous_state"] = None
        self.flow_state["first_round"] = True

    def determine_current_state(self):
        """ Determine the current state of the flow."""
        previous_state = self.flow_state["previous_state"]
        
        if previous_state is None:
            return "Coder"
        
        elif previous_state == "Coder":
            return "Interpreter"
            
        elif previous_state == "Interpreter":
            if self.flow_state["finish"] and not self.flow_state["first_round"]:
                curr_state = "GenerateReply"
            else:
                curr_state = "Coder"
            self.flow_state["first_round"] = False
            return curr_state
        
        elif "GenerateReply":
            return None
        
        else:
            raise ValueError(f"Invalid state: {previous_state}")
                        
    def call_coder(self):
        """ Call the coder subflow."""
        if self.flow_state["previous_state"] is None:
            input_interface = self.first_input_interface_coder
        else:
            input_interface = self.input_interface_coder
        
        message = self.package_input_message(
            data = input_interface(self.flow_state),
            dst_flow = "Coder"
        )
        self.subflows["Coder"].get_reply(
            message,
        )
        
    def call_interpreter(self):
        """ Call the interpreter subflow."""
        input_interface = self.input_interface_interpreter
        
        message = self.package_input_message(
            data = input_interface(self.flow_state),
            dst_flow = "Interpreter"
        )
        
        self.subflows["Interpreter"].get_reply(
                message,
        )
        
    def generate_reply(self):
          
        input_interface = self.input_interface_generate_reply
          
        reply = self.package_output_message(
            input_message=self.flow_state["initial_message"],
            response=input_interface(self.flow_state),
        )
        self.send_message(reply)
        
    def register_data_to_state(self, input_message):
        """ Register the data from the input message to the flow state."""
        previous_state = self.flow_state["previous_state"]
        
        #first call to flow
        if previous_state is None:
            #register initial message so we can reply to it later
            self.flow_state["initial_message"] = input_message
            #register the question
            self.flow_state["goal"] = input_message.data["goal"]
        
        elif previous_state == "Coder":
            self.flow_state["code"] = input_message.data["code"]
            self.flow_state["language_of_code"] = input_message.data["language_of_code"]
            self.flow_state["finish"] = input_message.data["finish"]
        
        #case where our last call was to the safeguard
        elif previous_state == "Interpreter":
            self.flow_state["interpreter_output"] = input_message.data["interpreter_output"]

   
    def run(self, input_message: FlowMessage):
        """ Run the flow."""
        self.register_data_to_state(input_message)
        
        current_state = self.determine_current_state()
        
        #call the appropriate function based on the current state
        if current_state == "Coder":
            self.call_coder()
            
        elif current_state == "Interpreter":
            self.call_interpreter()
            
        elif current_state == "GenerateReply":
            self.generate_reply()
        
        self.flow_state["previous_state"] = current_state if current_state != "GenerateReply" else None
