from abc import ABC
from typing import List, Dict, Any, Union

import colorama

from src import utils
from src.messages import InputMessage, OutputMessage, FlowMessage, Message

log = utils.get_pylogger(__name__)


class Flow(ABC):
    # metadata
    name: str
    description: str
    flow_type: str
    flow_run_id: str
    verbose: bool

    # state of the flow
    state: Dict[str, Any]
    history: List[Message]

    def __init__(
            self,
            name: str,
            description: str,
            verbose: bool = False):

        self.name = name
        self.description = description
        self.verbose = verbose

        self.initialize()

    def initialize(self, api_key: str = None):
        self.state = {}
        self.history = []
        self.flow_run_id = utils.general_helpers.create_unique_id()
        if api_key:
            self.set_api_key(api_key=api_key)

        # ToDo: log initialize message?

    # ToDo: dump and load are just placeholders
    # maybe we tell the user to return an object that can be pickled (that would allow storing subflows in the state)
    def dump(self):
        return {
            "state": self.state,
            "history": self.history,
            "name": self.name,
            "description": self.description,
            "flow_type": self.flow_type,
            "flow_run_id": self.flow_run_id,
            "verbose": self.verbose
        }

    def load(self, data):
        self.state = data["state"]
        self.history = data["history"]
        self.name = data["name"]
        self.description = data["description"]
        self.flow_type = data["flow_type"]
        self.flow_run_id = data["flow_run_id"]
        self.verbose = data["verbose"]

    def expected_fields_in_state(self):
        # a concrete implementation should return a list of expected inputs given the current state
        raise NotImplementedError()

    def assert_state_valid(self):
        for expected_field in self.expected_fields_in_state():
            assert (
                    expected_field in self.state
            ), f"The state of the flow {self.name} must contain the field {expected_field}"

    def update_state(self, data: Union[Dict[str, Any], Message], keys: List[str] = None):
        # unwrap message
        if isinstance(data, Message):
            data = data.data

        if keys is None:
            keys = data.keys()

        for key in keys:
            self.state[key] = data[key]

        self.assert_state_valid()

        # ToDo: log state update message

    def _log_message(self, message: Message):
        if self.verbose:
            # state_str = pprint.pformat(self.state, indent=4)
            log.info(
                f"\n{colorama.Fore.RED} ~~~ Logging to history "
                f"[{self.name} -- {self.flow_run_id}] ~~~"
                f"\n{colorama.Fore.WHITE}Content: {message.content}"
                # f"\nCurrent state: {state_str}{colorama.Style.RESET_ALL}"
            )
        return self.history.append(message)

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

    def step(self) -> bool:
        # update the flow by one step
        raise NotImplementedError()

    def run(self, taskMessage: TaskMessage):

        # log task message
        self._log_message(taskMessage)
        self.update_state(taskMessage)

        # after the run is completed, the expectedOutputs must be keys in the state
        expected_outputs = taskMessage.expectedOutputs

        while True:
            finished = self.step()
            if finished:
                break

        # package output message
        output_message = self._package_output_message(expected_outputs=expected_outputs)
        return output_message


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
