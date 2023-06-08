import copy
from abc import ABC
from typing import List, Dict, Any, Union

import colorama

import src.flows
from src import utils
from src.history import FlowHistory
from src.messages import OutputMessage, Message, StateUpdateMessage, TaskMessage
from src.utils import general_helpers

log = utils.get_pylogger(__name__)


class Flow(ABC):
    KEYS_TO_IGNORE_CKPT = ["flow_run_id"]
    KEYS_TO_IGNORE_HASH = ["name", "description", "verbose", "flow_run_id", "history", "_init_attributes"]

    name: str
    description: str
    expected_inputs: List[str]
    expected_outputs: List[str]
    verbose: bool
    dry_run: bool
    flow_run_id: str
    history: FlowHistory

    def __init__(
            self,
            **kwargs
    ):
        self.name = kwargs.pop("name")
        self.description = kwargs.pop("description")
        self.expected_inputs = kwargs.pop("expected_inputs", [])
        self.expected_outputs = kwargs.pop("expected_outputs", [])
        self.flow_type = kwargs.pop("flow_type", "flow")
        self.verbose = kwargs.pop("verbose", False)
        self.dry_run = kwargs.pop("dry_run", False)

        self._init_attributes = copy.deepcopy(self.__dict__)

        self.initialize(**kwargs)

    def initialize(self, **kwargs):
        for key, val in self._init_attributes.items():
            self.__setattr__(key, val)

        for key, value in kwargs.items():
            if key not in self._init_attributes:
                self.__setattr__(key, value)

        self.history = FlowHistory()
        self.flow_run_id = general_helpers.create_unique_id()

    def __getstate__(self):
        state = {k: v for k, v in self.__dict__.items() if k not in self.KEYS_TO_IGNORE_CKPT}
        return state

    def __setstate__(self, state):
        for k, v in state.items():
            if k not in self.KEYS_TO_IGNORE_CKPT:
                super().__setattr__(k, v)
        # self.flow_run_id = general_helpers.create_unique_id()

    def __repr__(self):
        keys_to_ignore = self.KEYS_TO_IGNORE_HASH + self.expected_output_keys
        run_state = {k: v for k, v in self.__dict__.items() if k not in keys_to_ignore}
        return repr(run_state)

    def expected_inputs_given_state(self):
        return self.expected_inputs

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
                f"[{self.name} -- {self.flow_run_id}] ~~~"
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
            if key in self.__dict__:
                if value is None or value == self.__dict__[key]:
                    continue

            updates[key] = value
            self.__setattr__(key, value)

        state_update_message = StateUpdateMessage(
            message_creator=self.name,
            parent_message_ids=parent_message_ids,
            flow_runner=self.name,
            flow_run_id=self.flow_run_id,
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
            if expected_key not in self.__dict__:
                missing_keys.append(expected_key)
                continue

            output_data[expected_key] = self.__dict__[expected_key]

        error_message = None
        if missing_keys:
            error_message = f"The state of {self.name} [flow run ID: {self.flow_run_id}] does not contain" \
                            f"the following expected keys: {missing_keys}."

        return OutputMessage(
            message_creator=self.name,
            parent_message_ids=parent_message_ids,
            flow_runner=self.name,
            flow_run_id=self.flow_run_id,
            data=output_data,
            error_message=error_message
        )

    def step(self) -> bool:
        return True

    def run(self, expected_output_keys: List[str] = None):
        while True:
            finished = self.step()
            if finished:
                break

    def package_task_message(self, recipient_flow: src.flows.Flow,
                  task_name: str, task_data: Dict[str, Any], expected_output_keys: List[str],
                  parent_message_ids: List[str] = None):
        return TaskMessage(
            flow_runner=self.name,
            flow_run_id=self.flow_run_id,
            message_creator=self.name,
            target_flow_run_id=recipient_flow.flow_run_id,
            parent_message_ids=parent_message_ids,
            task_name=task_name,
            data=task_data,
            expected_output_keys=expected_output_keys
        )

    def __call__(self, task_message: TaskMessage):
        # ~~~ check and log input ~~~
        self._check_input_validity(task_message)
        self._log_message(task_message)
        self._update_state(task_message)

        # ~~~ After the run is completed, the expected_output_keys must be keys in the state ~~~
        expected_output_keys = task_message.expected_output_keys
        if expected_output_keys is None:
            expected_output_keys = self.expected_outputs
        self.expected_output_keys = expected_output_keys

        # ~~~ Execute the logic of the flow, it should populate state with expected_output_keys ~~~
        self.run()

        # ~~~ Package output message ~~~
        return self._package_output_message(expected_output_keys=self.expected_output_keys,
                                            parent_message_ids=[task_message.message_id])


class AtomicFlow(Flow, ABC):

    def __init__(
            self,
            **kwargs
    ):
        kwargs["flow_type"] = "atomic-flow"
        super().__init__(**kwargs)


class CompositeFlow(Flow, ABC):

    def __init__(
            self,
            **kwargs
    ):
        kwargs["flow_type"] = "composite-flow"
        super().__init__(**kwargs)

    def call(self, flow:Flow):
        pass

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
