
from aiflows.messages import FlowMessage
from aiflows.interfaces import KeyInterface
from flow_modules.aiflows.ChatInteractiveFlowModule import ChatHumanFlowModule

class HumanToHuman(ChatHumanFlowModule):
    def __init__(**kwargs):
        super().__init__(**kwargs)
        self.input_interface_user = KeyInterface( keys_to_rename = {"human_input": "api_output"}) 
