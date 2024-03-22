
from aiflows.base_flows import AtomicFlow
from aiflows.messages import FlowMessage
from flow_modules.aiflows.ChatFlowModule import ChatAtomicFlow
import json


class CodeGenerator(ChatAtomicFlow):

    def run(self, input_message: FlowMessage):
        input_data = input_message.data
        json_parsable = False
        response = None
        
        #ensure the response is json parsable
        while not json_parsable:
            
            output = self.query_llm(input_data=input_data).strip()
            
            try:
                response = json.loads(output)
                json_parsable = True
            
            except (json.decoder.JSONDecodeError, json.JSONDecodeError):
                
                feedback = "The previous response cannot be parsed with json.loads, it \
                    could be the backslashes used for escaping single quotes in the string arguments of the code are not properly \
                        escaped themselves within the JSON context. Next time, do not provide any comments or code blocks. \
                            Make sure your next response is purely json parsable."
                previous_code = output
                new_input_data = input_data.copy()
                new_input_data = {
                    "goal": input_data["goal"],
                    "feedback": feedback,
                    "previous_code": previous_code,   
                }
                input_data = new_input_data

        
        reply = self.package_output_message(
            input_message = input_message,
            response = response
        )
        self.send_message(reply)
        
