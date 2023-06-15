import copy
from abc import ABC
from typing import List, Dict, Any, Union

import colorama

import flows
from flows import utils
from flows.history import FlowHistory
from flows.messages import OutputMessage, Message, StateUpdateMessage, TaskMessage
from flows.utils.general_helpers import create_unique_id

log = utils.get_pylogger(__name__)


class Flow(ABC):
    KEYS_TO_IGNORE_HASH = ["name", "description", "verbose", "history", "repository_id", "class_name"]

    name: str
    description: str
    expected_inputs: List[str]
    expected_outputs: List[str]
    flow_type: str
    verbose: bool
    dry_run: bool
    namespace_clearing_after_run: bool

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
            "flow_type": kwargs.pop("flow_type", "Flow"),
            "verbose": kwargs.pop("verbose", True),
            "dry_run": kwargs.pop("dry_run", False),
            "namespace_clearing_after_run": kwargs.pop("namespace_clearing_after_run", True)
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
    def get_config(cls, **overrides):
        return flows.flow_verse.load_config(cls.repository_id,
                                            cls.class_name,
                                            **overrides)

    @classmethod
    def instantiate(cls, config):
        return cls(**config)

    def reset(self, full_reset: bool = True):
        # ~~~ What should be kept ~~~
        state = self.__getstate__()
        flow_run_id = self.flow_run_id

        # ~~~ Complete erasure ~~~
        self.__dict__ = {}

        # ~~~ Restore what should be kept ~~~
        if full_reset:
            self.flow_config = state["flow_config"]
            self.__set_config_params()
        else:
            self.__setstate__(state)
            self.flow_run_id = flow_run_id

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
            self.flow_state[key] = copy.deepcopy(value)

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
        self.flow_run_id = create_unique_id()

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
        # We don't log it to history to not see it in the visualization
        self.flow_state["api_key"] = api_key
        # self._update_state(update_data={"api_key": str(api_key)})

    def _log_message(self, message: Message):
        if self.verbose:
            log.info(
                f"\n{colorama.Fore.RED} ~~~ Logging to history "
                f"[{self.name} -- {self.flow_run_id}] ~~~\n"
                f"{colorama.Fore.WHITE}Message being logged: {str(message)}{colorama.Style.RESET_ALL}"
            )
        return self.flow_state["history"].add_message(message)

    def _get_keys_from_state(self, keys: List[str], allow_class_namespace: bool = True):
        data = {}
        for key in keys:
            if key in self.flow_state:
                data[key] = self.flow_state[key]
                continue

            if allow_class_namespace:
                if key in self.__dict__:
                    data[key] = self.__dict__[key]
        return data

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
            data=copy.deepcopy(outputs),
            error_message=error_message,
            history=self.flow_state.get("history", [])
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
            data=copy.deepcopy(task_data),
            expected_outputs=expected_outputs
        )

    def run(self, input_data: Dict[str, Any], expected_outputs: List[str]) -> Dict[str, Any]:
        raise NotImplementedError

    def __call__(self, task_message: TaskMessage):
        # ~~~ check and log input ~~~
        if "api_key" in task_message.data:
            self.set_api_key(api_key=task_message.data["api_key"])
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
        if self.namespace_clearing_after_run:
            self._clear()

        return output_message


class AtomicFlow(Flow, ABC):

    def __init__(
            self,
            **kwargs
    ):
        if "flow_type" not in kwargs:
            kwargs["flow_type"] = "AtomicFlow"
        super().__init__(**kwargs)


class CompositeFlow(Flow, ABC):
    flows: Dict[str, Union[Dict[str, Any], Flow]]
    early_exit_key: str

    def __init__(
            self,
            **kwargs
    ):
        if "early_exit_key" not in kwargs:
            kwargs["early_exit_key"] = None

        if "flow_type" not in kwargs:
            kwargs["flow_type"] = "CompositeFlow"

        super().__init__(**kwargs)

    def _init_flow(self, flow):
        init_flow = flow.__class__.load_from_config(flow.flow_config)

        if "api_key" in self.flow_state:
            init_flow.set_api_key(api_key=self.flow_state["api_key"])

        return init_flow

    def _early_exit(self):
        if self.early_exit_key:
            if self.early_exit_key in self.flow_state:
                return bool(self.flow_state[self.early_exit_key])
            elif self.early_exit_key in self.__dict__:
                return bool(self.__dict__[self.early_exit_key])

        return False

    def _call_flow_from_state(
            self,
            flow: Flow,
            expected_outputs: list[str] = None,
            parent_message_ids: List[str] = None,
            search_class_namespace_for_inputs: bool = True
    ):
        # ~~~ Prepare the call ~~~
        task_data = self._get_keys_from_state(
            keys=flow.expected_inputs_given_state(),
            allow_class_namespace=search_class_namespace_for_inputs
        )

        task_message = self.package_task_message(
            recipient_flow=flow,
            task_name="",
            task_data=task_data,
            expected_outputs=expected_outputs,
            parent_message_ids=parent_message_ids
        )
        self._log_message(task_message)

        # ~~~ Execute the call ~~~
        answer_message = flow(task_message)

        # ~~~ Logs message to history ~~~
        self._log_message(answer_message)

        return answer_message
