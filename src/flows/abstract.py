from abc import ABC
from typing import List, Dict, Any, Union
import colorama

from src.history import FlowHistory
from src.messages import OutputMessage, Message, StateUpdateMessage, TaskMessage
from src.utils import general_helpers
import src.utils as utils

log = utils.get_pylogger(__name__)


class Flow(ABC):
    name: str
    description: str
    expected_inputs: List[str]
    expected_outputs: List[str]
    verbose: bool

    # ~~~ Encapsulate the logic of run ~~~
    state: Dict[str, Any]
    history: FlowHistory

    def __init__(
            self,
            name: str,
            description: str,
            expected_inputs: List[str],
            expected_outputs: List[str],
            verbose: bool = False,
            **kwargs
    ):
        self.name = name
        self.description = description
        self.expected_inputs = list(expected_inputs) if expected_inputs else []
        self.expected_outputs = list(expected_outputs) if expected_outputs else []
        self.verbose = verbose

    def initialize(self, **kwargs):
        self.state = {"name":self.name, "flow_run_id": general_helpers.create_unique_id()}
        self.history = FlowHistory()

    def expected_inputs_given_state(self):
        return self.expected_outputs

    def set_api_key(self, api_key: str):
        self._update_state(update_data={"api_key": str(api_key)})

    def _check_input_validity(self, task_message: TaskMessage):
        for expected_input in self.expected_inputs_given_state():
            assert (
                    expected_input in task_message.data
            ), f"The input message to the flow {self.name} must contain the field {expected_input}"

    def _log_message(self, message: Message):
        if self.verbose:
            log.info(
                f"\n{colorama.Fore.RED} ~~~ Logging to history "
                f"[{self.name} -- {self.state['flow_run_id']}] ~~~"
                f"\n{colorama.Fore.WHITE}Message being logged: {str(message)}{colorama.Style.RESET_ALL}"
            )
        return self.history.add_message(message)

    def _update_state(self, update_data: Union[Dict[str, Any], Message], parent_message_ids: List[str] = None):
        if isinstance(update_data, Message):
            update_data = update_data.data

        if not parent_message_ids:
            parent_message_ids = []

        if not update_data:
            log.warning("Updating states called with empty updates")
            return

        updates = {}
        for key, value in update_data.items():
            if key in self.state:
                if value is None or value == self.state[key]:
                    continue

            updates[key] = value
            self.state[key] = value

        state_update_message = StateUpdateMessage(
            message_creator=self.state["name"],
            parent_message_ids=parent_message_ids,
            flow_runner=self.state["name"],
            flow_run_id=self.state["flow_run_id"],
            updated_keys=list(updates.keys()),
            data=updates,
        )
        return self._log_message(state_update_message)

    def _package_output_message(
        self,
        expected_output_keys: List[str],
        parent_message_ids: List[str]
    ):

        output_data = {}
        missing_keys = []
        for expected_key in expected_output_keys:
            if expected_key not in self.state:
                missing_keys.append(expected_key)
                continue

            output_data[expected_key] = self.state[expected_key]

        error_message = None
        if missing_keys:
            error_message = f"The state of {self.name} [flow run ID: {self.state['flow_run_id']}] does not contain" \
                            f"the following expected keys: {missing_keys}."

        return OutputMessage(
            message_creator=self.name,
            parent_message_ids=parent_message_ids,
            flow_runner=self.name,
            flow_run_id=self.state["flow_run_id"],
            data=output_data,
            error_message=error_message
        )

    def step(self) -> bool:
        return True

    def run(self, task_message: TaskMessage):
        while True:
            finished = self.step()
            if finished:
                break

    def __call__(self, task_message: TaskMessage):
        # ~~~ check and log input ~~~
        self._check_input_validity(task_message)
        self._log_message(task_message)
        self._update_state(task_message)

        # ~~~ After the run is completed, the expected_output_keys must be keys in the state ~~~
        expected_output_keys = task_message.expected_output_keys
        if expected_output_keys is None:
            expected_output_keys = self.expected_outputs
        self.state["expected_output_keys"] = expected_output_keys

        # ~~~ Execute the logic of the flow, it should populate state with expected_output_keys ~~~
        self.run(task_message=task_message)

        # ~~~ Package output message ~~~
        output_message = self._package_output_message(expected_output_keys=self.state["expected_output_keys"],
                                                      parent_message_ids=[task_message.message_id])
        return output_message


class AtomicFlow(Flow, ABC):

    def __init__(
            self,
            name: str,
            description: str,
            expected_inputs: List[str],
            expected_outputs: List[str],
            verbose: bool = False,
            **kwargs
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

    def initialize(self):
        super().initialize()

    def _call_flow(self, flow_id: str, expected_output_keys: list[str] = None, parent_message_ids: List[str] = None):
        # ~~~ Prepare the call ~~~
        flow = self.flows[flow_id]
        call_inputs = {k: self.state[k] for k in flow.expected_inputs_given_state()}

        task_message = TaskMessage(
            expected_output_keys=expected_output_keys,
            target_flow_run_id=flow.state["flow_run_id"],
            message_creator=self.name,
            parent_message_ids=parent_message_ids,
            flow_runner=self.name,
            flow_run_id=self.state["flow_run_id"],
            data=call_inputs,
        )
        self._log_message(task_message)

        # ~~~ Execute the call ~~~
        answer_message = flow(task_message)

        # ~~~ Logs message to history ~~~
        self._log_message(answer_message)
        self._update_state(answer_message)

        return answer_message


