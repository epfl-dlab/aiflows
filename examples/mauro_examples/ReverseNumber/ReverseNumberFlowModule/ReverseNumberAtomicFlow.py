from aiflows.base_flows import AtomicFlow


class ReverseNumberAtomicFlow(AtomicFlow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    # Customize the logic within this function as needed for your specific flow requirements.
    def run(self, input_message) -> None:
        print("Called ReverseNumberAtomic", "\n", "state", self.flow_state)
        input_number = input_message.data["number"]
        output_number = int(str(input_number)[::-1])
        response_data = {"output_number": output_number}
        response = self._package_output_message(input_message, response_data)
        self.reply(response, input_message)
