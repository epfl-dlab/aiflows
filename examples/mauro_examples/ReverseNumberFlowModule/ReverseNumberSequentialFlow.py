from aiflows.base_flows import CompositeFlow
from aiflows.interfaces.key_interface import KeyInterface
from aiflows import logging

# logging.set_verbosity_debug()  # Uncomment this line to see verbose logs


class ReverseNumberSequentialFlow(CompositeFlow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.transformation_1 = KeyInterface(
            keys_to_rename={"output_number": "number"},
            keys_to_select=["number"],
        )
        self.transformation_2 = KeyInterface(
            keys_to_select=["output_number"],
        )
        self.get_next_call = {
            "first_reverse_flow": "second_reverse_flow",
            "second_reverse_flow": "reply_to_message",
            "reply_to_message": "first_reverse_flow",
        }

    def set_up_flow_state(self):
        super().set_up_flow_state()
        self.flow_state = {"current_call": "first_reverse_flow"}

    # Customize the logic within this function as needed for your specific flow requirements.
    def run(self, input_message):
        print("Called ReverseNumberSequential", "\n", "state", self.flow_state)

        curr_call = self.flow_state["current_call"]

        if curr_call == "first_reverse_flow":
            self.flow_state["initial_message"] = input_message
            self.subflows["first_reverse_flow"].get_reply(input_message)

        elif curr_call == "second_reverse_flow":
            message = self.package_input_message(
                self.transformation_1(input_message).data
            )
            self.subflows["second_reverse_flow"].get_reply(message)

        else:
            message = self.transformation_2(input_message)
            reply = self.package_output_message(
                input_message=self.flow_state["initial_message"], response=message.data
            )
            self.send_message(reply)

        self.flow_state["current_call"] = self.get_next_call[curr_call]
