import copy
from abc import ABC
from typing import List, Dict, Any, Union

import colorama

from src import utils
from src.history import FlowHistory
from src.messages import OutputMessage, Message, StateUpdateMessage, TaskMessage
from src.utils import io_utils
from src.utils.general_helpers import create_unique_id

log = utils.get_pylogger(__name__)


class Flow(ABC):
    KEYS_TO_IGNORE_HASH = ["name", "description", "verbose", "history"]

    name: str
    description: str
    expected_inputs: List[str]
    expected_outputs: List[str]
    flow_type: str
    verbose: bool
    dry_run: bool

    flow_run_id: str
    flow_config: Dict[str, Any]
    flow_state: Dict[str, Any]

    def __init__(
            self,
            **kwargs
    ):

        # ~~~ Flow Config parameter to reconstruct the object ~~~
        self.flow_config = {
            "name": kwargs.pop("name"),
            "description": kwargs.pop("description"),
            "expected_inputs": kwargs.pop("expected_inputs", []),
            "expected_outputs": kwargs.pop("expected_outputs", []),
            "flow_type": kwargs.pop("flow_type", "flow"),
            "verbose": kwargs.pop("verbose", True),
            "dry_run": kwargs.pop("dry_run", False)
        }

        self.flow_config.update(copy.deepcopy(kwargs))
        self.__set_config_params()

        self.flow_state = {
            "history": FlowHistory()
        }

        self.flow_run_id = create_unique_id()

    def __set_config_params(self):
        for k, v in self.flow_config.items():
            self.__setattr__(k, copy.deepcopy(v))

    @classmethod
    def load_from_config(cls, flow_config: Dict[str, Any]):
        return cls(**flow_config)

    @classmethod
    def load_from_state(cls, flow_state: Dict):
        flow_config = flow_state["flow_config"]
        flow = cls.load_from_config(flow_config=flow_config)
        flow.__setstate__(flow_state)
        return flow

    @classmethod
    def load_from_checkpoint(cls, ckpt_path: str):
        data = io_utils.load_pickle(ckpt_path)
        return cls.load_from_state(data)

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
            if key in self.flow_state:
                if value is None or value == self.flow_state[key]:
                    continue

            updates[key] = value
            self.flow_state[key] = value

        if updates:
            state_update_message = StateUpdateMessage(
                message_creator=self.name,
                parent_message_ids=parent_message_ids,
                flow_runner=self.name,
                flow_run_id=self.flow_run_id,
                updated_keys=list(updates.keys()),
                # data=updates.keys(),
                # TODO: do we prefer to keep all the data in the message, rather than modified keys
            )
            return self._log_message(state_update_message)

    def __getstate__(self):
        return {
            "flow_config": copy.deepcopy(self.flow_config),
            "flow_state": copy.deepcopy(self.flow_state),
            "config_param_updates": {k: self.__dict__[k]
                                     for k in self.flow_config if self.flow_config[k] != self.__dict__[k]}
        }

    def __setstate__(self, state):
        self.flow_config = copy.deepcopy(state["flow_config"])
        self.__set_config_params()
        self.flow_state = copy.deepcopy(state["flow_state"])
        for k, v in state["config_param_updates"].items():
            self.__setattr__(k, copy.deepcopy(v))


    def __repr__(self):
        flow_config_to_keep = set(self.flow_config.keys()) - set(self.KEYS_TO_IGNORE_HASH)
        config_hashing_params = {k: v for k, v in self.__dict__.items() if k in flow_config_to_keep}
        state_hashing_params = {k: v for k, v in self.flow_state.items() if k not in self.KEYS_TO_IGNORE_HASH}
        hash_dict = {"flow_config": config_hashing_params, "flow_state": state_hashing_params}
        return repr(hash_dict)

    def _clear(self):
        # ~~~ What should be kept ~~~
        state = self.__getstate__()
        flow_run_id = self.flow_run_id

        # ~~~ Complete erasure ~~~
        self.__dict__ = {}

        # ~~~ Restore what should be kept ~~~
        self.__setstate__(state)
        self.flow_run_id = flow_run_id

    def expected_inputs_given_state(self):
        return self.expected_inputs

    def set_api_key(self, api_key: str):
        self._update_state(update_data={"api_key": str(api_key)})

    def _log_message(self, message: Message):
        if self.verbose:
            log.info(
                f"\n{colorama.Fore.RED} ~~~ Logging to history "
                f"[{self.name} -- {self.flow_run_id}] ~~~\n"
                f"{colorama.Fore.WHITE}Message being logged: {str(message)}{colorama.Style.RESET_ALL}"
            )
        return self.flow_state["history"].add_message(message)

    def _package_output_message(
            self,
            outputs: Dict[str, Any],
            expected_outputs: List[str],
            parent_message_ids: List[str]
    ):
        missing_keys = []
        for expected_key in expected_outputs:
            if expected_key not in outputs:
                missing_keys.append(expected_key)
                continue

        error_message = None
        if missing_keys:
            error_message = f"The state of {self.name} [flow run ID: {self.flow_run_id}] does not contain" \
                            f"the following expected keys: {missing_keys}."

        return OutputMessage(
            message_creator=self.name,
            parent_message_ids=parent_message_ids,
            flow_runner=self.name,
            flow_run_id=self.flow_run_id,
            data=outputs,
            error_message=error_message
        )

    def package_task_message(
            self,
            recipient_flow: "Flow",
            task_name: str,
            task_data: Dict[str, Any],
            expected_outputs: List[str],
            parent_message_ids: List[str] = None
    ):
        return TaskMessage(
            flow_runner=self.name,
            flow_run_id=self.flow_run_id,
            message_creator=self.name,
            target_flow_run_id=recipient_flow.flow_run_id,
            parent_message_ids=parent_message_ids,
            task_name=task_name,
            data=task_data,
            expected_outputs=expected_outputs
        )

    def run(self, input_data: Dict[str, Any], expected_outputs: List[str]) -> Dict[str, Any]:
        raise NotImplementedError

    def __call__(self, task_message: TaskMessage):
        # ~~~ check and log input ~~~
        # self._check_input_validity(task_message)
        self._log_message(task_message)

        # ~~~ After the run is completed, the expected_outputs must be keys in the state ~~~
        expected_outputs = task_message.expected_outputs
        if expected_outputs is None:
            expected_outputs = self.expected_outputs

        # ~~~ Execute the logic of the flow, it should populate state with expected_outputs ~~~
        outputs = self.run(input_data=task_message.data, expected_outputs=expected_outputs)

        # ~~~ Package output message ~~~
        output_message = self._package_output_message(
            outputs=outputs,
            expected_outputs=expected_outputs,
            parent_message_ids=[task_message.message_id]
        )

        # ~~~ destroying all attributes that are not flow_state or flow_config ~~~
        self._clear()

        return output_message


# class StepFlow(Flow):
#     def step(self) -> bool:
#         raise NotImplementedError
#
#     def run(self, input_data: Dict[str, Any], expected_outputs: List[str]):
#         # log to state input_data, expected_outputs
#         while True:
#             finished = self.step()
#             if finished:
#                 break


class AtomicFlow(Flow, ABC):

    def __init__(
            self,
            **kwargs
    ):
        kwargs["flow_type"] = "atomic-flow"
        super().__init__(**kwargs)


class CompositeFlow(Flow, ABC):
    flows: Dict[str, Union[Dict[str, Any], Flow]]

    def __init__(
            self,
            **kwargs
    ):
        kwargs["flow_type"] = "composite-flow"
        super().__init__(**kwargs)
        self.flow_state["flows"] = kwargs.pop("flows", {})

    def _call_flow(
            self,
            flow: Flow,
            expected_outputs: list[str] = None,
            parent_message_ids: List[str] = None
    ):
        # ~~~ Prepare the call ~~~
        call_inputs = {k: self.__getattribute__(k) for k in flow.expected_inputs_given_state()}

        task_message = TaskMessage(
            expected_outputs=expected_outputs,
            target_flow_run_id=flow.flow_run_id,
            message_creator=self.name,
            parent_message_ids=parent_message_ids,
            flow_runner=self.name,
            flow_run_id=self.flow_run_id,
            data=call_inputs,
        )
        self._log_message(task_message)

        # ~~~ Execute the call ~~~
        answer_message = flow(task_message)

        # ~~~ Logs message to history ~~~
        self._log_message(answer_message)

        return answer_message
