from abc import ABC
from typing import List, Dict, Any
import colorama

from src.history import FlowHistory
from src.messages import InputMessage, OutputMessage, FlowMessage, FlowUpdateMessage, Message
from src import utils

log = utils.get_pylogger(__name__)


class Flow(ABC):
    name: str
    description: str
    expected_inputs: List[str]
    expected_outputs: List[str]
    flow_type: str
    history: FlowHistory
    state: Dict[str, Any]
    flow_run_id: str
    verbose: bool

    def __init__(
            self,
            name: str,
            description: str,
            expected_inputs: List[str],
            expected_outputs: List[str],
            verbose: bool = False,
            state: Dict[str, Any] = None):

        self.name = name
        self.description = description
        self.expected_inputs = list(expected_inputs) if expected_inputs else []
        self.expected_outputs = list(expected_outputs) if expected_outputs else []
        self.verbose = verbose

        self.initialize()

        if state:
            self.state = state

    def initialize(self, api_key: str = None):
        self.state = {}
        self.history = FlowHistory()
        self.flow_run_id = utils.general_helpers.create_unique_id()
        if api_key:
            self.set_api_key(api_key=api_key)

    def expected_inputs_given_state(self):
        return self.expected_inputs

    def _check_input_validity(self, input_message: InputMessage):
        for expected_input in self.expected_inputs_given_state():
            assert (
                    expected_input in input_message.inputs
            ), f"The input message to the flow {self.name} must contain the field {expected_input}"

    def _log_message(self, message: Message):
        if self.verbose:
            # state_str = pprint.pformat(self.state, indent=4)
            log.info(
                f"\n{colorama.Fore.RED} ~~~ Logging to history "
                f"[{self.name} -- {self.flow_run_id}] ~~~"
                f"\n{colorama.Fore.WHITE}Content: {message.content}"
                # f"\nCurrent state: {state_str}{colorama.Style.RESET_ALL}"
            )
        return self.history.add_message(message)

    def _log_input(self, input_message: InputMessage = None):
        if input_message is None:
            return

        self._check_input_validity(input_message=input_message)

        input_states = {key: message.content for key, message in input_message.inputs.items() if key in self.expected_inputs_given_state()}
        self._update_states(to_update_dict=input_states)
        # for inp_key, inp_value in input_message.inputs.items():
        #     self._update_state(key=inp_key, value=inp_value.content)

        fields = input_message.soft_copy()
        local_input_message = InputMessage(**fields)
        return self._log_message(local_input_message)

    def _log_update(self, content: str, message_creator: str = None, parents: List = None):
        if parents is None:
            parents = []

        if message_creator is None:
            message_creator = self.name

        update_message = FlowUpdateMessage(
            flow_run_id=self.flow_run_id,
            flow_runner=self.name,
            message_creator=message_creator,
            content=content,
            parents=parents,
            current_flow_state=self.state
        )
        return self._log_message(update_message)

    def _update_states(self, to_update_dict: Dict[str, Any], parents: List[str] = None):
        if not hasattr(self, "state"):
            self.state = {}

        if not to_update_dict:
            log.warning("Updating states called with empty updates")
            return

        updated_keys = []
        for key, value in to_update_dict.items():
            if value is not None:
                # ~~~ No need to update if already set ~~~
                if key in self.state:
                    if self.state[key].content == value:
                        return

                updated_keys.append(key)
                self.state[key] = FlowMessage(
                    flow_run_id=self.flow_run_id,
                    flow_runner=self.name,
                    message_creator=self.name,
                    content=value,
                    parents=parents
                )

        log_message_content = f"State of flow {self.name} [run-id: {self.flow_run_id}] " \
                              f"updated the following keys: {updated_keys}."
        self._log_update(content=log_message_content, parents=parents)

    def _package_output_message(
            self,
            expected_outputs: List[str],
            parsed_outputs: Dict[str, FlowMessage],
            parents: List[str]
    ):

        valid_parsing = True
        for expected_key in expected_outputs:
            if expected_key not in parsed_outputs:
                valid_parsing = False
                break

        return OutputMessage(
            parsed_outputs=parsed_outputs,
            valid_parsing=valid_parsing,
            message_creation_history=self.history,
            flow_run_id=self.flow_run_id,
            flow_runner=self.name,
            message_creator=self.name,
            content=f"Output of flow {self.name} [flow run ID: {self.flow_run_id}]",
            parents=parents,
            current_flow_state=self.state
        )

    def set_api_key(self, api_key: str):
        self._update_states(to_update_dict={"api_key": str(api_key)})

    def _flow(self, *args, **kwargs):
        raise NotImplementedError

    def run(self, input_message: InputMessage = None, expected_outputs: List[str] = None, **kwargs) -> OutputMessage:
        self._log_input(input_message=input_message)

        if expected_outputs is None:
            expected_outputs = self.expected_outputs

        parsed_outputs = self._flow(input_message=input_message, expected_outputs=expected_outputs, **kwargs)

        parents = []
        if input_message:
            parents = [input_message.message_id]

        return self._package_output_message(
            expected_outputs=expected_outputs,
            parsed_outputs=parsed_outputs,
            parents=parents
        )


class AtomicFlow(Flow, ABC):

    def __init__(
        self,
        name: str,
        description: str,
        expected_inputs: List[str],
        expected_outputs: List[str],
        verbose: bool = False
    ):
        super().__init__(
            name=name,
            description=description,
            expected_inputs=expected_inputs,
            expected_outputs=expected_outputs,
            verbose=verbose)

        self.flow_type = "atomic-flow"


class CompositeFlow(Flow, ABC):
    flows: Dict[str, Flow]

    def __init__(
        self,
        name: str,
        description: str,
        expected_inputs: List[str],
        expected_outputs: List[str],
        flows: Dict[str, Flow],
        verbose: bool = False,
    ):
        self.flows = flows

        super().__init__(
            name=name,
            description=description,
            expected_inputs=expected_inputs,
            expected_outputs=expected_outputs,
            verbose=verbose)

        self.flow_type = "composite-flow"

    def initialize(self, api_key: str = None):
        super().initialize(api_key=api_key)
        self._initialize_flows(api_key=api_key)

    def _initialize_flows(self, api_key: str = None):
        for _, flow in self.flows.items():
            flow.initialize(api_key=api_key)

    def _read_answer_update_state(self, answer: OutputMessage):
        parsed_outputs = answer.parsed_outputs
        to_update = {key: message.content for key, message in parsed_outputs.items()}
        self._update_states(to_update_dict=to_update, parents=[answer.message_id])

    def _call_flow(self, flow_id: str, parents: List[str] = None):
        # ~~~ Prepare the call ~~~
        flow = self.flows[flow_id]

        input_message_description = f"Flow: {self.name} [flow run ID: {self.flow_run_id}] " \
                                    f"is calling subflow: {flow.name} [flow run ID: {flow.flow_run_id}]"

        print(f"expected: {flow.expected_inputs_given_state()}, available: {self.state.keys()}")
        call_inputs = {k: self.state[k] for k in flow.expected_inputs_given_state()}

        input_message = InputMessage(
            flow_run_id=self.flow_run_id,
            inputs=call_inputs,
            message_creator=self.name,
            flow_runner=self.name,
            content=input_message_description,
            target_flow=flow.flow_run_id,
            parents=parents
        )
        self._log_message(input_message)

        # ~~~ Execute the call ~~~
        answer_message = flow.run(input_message)
        return self._log_message(answer_message)
