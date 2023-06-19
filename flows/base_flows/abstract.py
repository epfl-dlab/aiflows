import os
import sys
import copy

from abc import ABC
from typing import List, Dict, Any, Union

import colorama
import hydra
from omegaconf import OmegaConf

import flows
from flows import utils
from flows.history import FlowHistory
from flows.messages import OutputMessage, Message, StateUpdateMessage, TaskMessage
from flows.utils.general_helpers import create_unique_id
from src.utils.general_helpers import recursive_dictionary_update

log = utils.get_pylogger(__name__)


class Flow(ABC):
    KEYS_TO_IGNORE_HASH = set(["name", "description", "verbose", "history", "repository_id", "class_name"])
    KEYS_TO_IGNORE_WHEN_RESETTING_NAMESPACE = set(["flow_config", "flow_state", "flow_run_id"])

    # ToDo: Document and remove. Here for reference
    # name: str
    # description: str
    # expected_inputs: List[str]
    # expected_outputs: List[str]
    # flow_type: str
    # verbose: bool
    # dry_run: bool
    # namespace_clearing_after_run: bool
    #
    # flow_run_id: str
    # flow_config: Dict[str, Any]
    # flow_state: Dict[str, Any]

    def __init__(
            self,
            **kwargs_passed_to_the_constructor
    ):
        self._extend_keys_to_ignore_when_resetting_namespace(list(kwargs_passed_to_the_constructor.keys()))
        self.__set_namespace_params(kwargs_passed_to_the_constructor)

        if self.flow_config.get("verbose", True):
            # ToDo: print the flow config with Rich
            pass

        self.set_up_flow_state()
        if isinstance(self, CompositeFlow):
            self.reset_flow_id(recursive=True)
        else:
            self.reset_flow_id()

    def _extend_keys_to_ignore_when_resetting_namespace(self, keys_to_ignore: List[str]):
        self.KEYS_TO_IGNORE_WHEN_RESETTING_NAMESPACE.update(keys_to_ignore)

    def _extend_keys_to_ignore_hash(self, keys_to_ignore: List[str]):
        self.KEYS_TO_IGNORE_HASH.update(keys_to_ignore)

    def __set_namespace_params(self, kwargs):
        for k, v in kwargs.items():
            if k == "flow_config":
                v = copy.deepcopy(v)  # Precautionary measure
            self.__setattr__(k, v)

    @classmethod
    def _validate_parameters(cls, config):
        if "flow_config" not in config:
            raise ValueError("flow_config is a required parameter.")

        flow_config = config["flow_config"]

        if "name" not in flow_config:
            raise ValueError("name is a required parameter in the flow_config.")
        if "description" not in flow_config:
            raise ValueError("description is a required parameter in the flow_config.")

    @classmethod
    def get_config(cls, **overrides):
        if cls == Flow:
            config = {
                "expected_inputs": [],
                "expected_outputs": [],
                "flow_type": "Flow",
                "verbose": True,
                "dry_run": False,
                "namespace_clearing_after_run": True,
            }
            return config
        elif cls == ABC:
            return {}
        elif cls == object:
            return {}

        # Recursively get the configs from the base classes
        super_cls = cls.__base__
        parent_default_config = super_cls.get_config()

        path_to_flow_directory = os.path.dirname(sys.modules[cls.__module__].__file__)
        class_name = cls.__name__

        path_to_config = os.path.join(path_to_flow_directory, f"{class_name}.yaml")
        if os.path.exists(path_to_config):
            default_config = OmegaConf.to_container(
                OmegaConf.load(path_to_config),
                resolve=True
            )
            config = recursive_dictionary_update(parent_default_config, default_config)
        elif overrides.get("verbose", True):
            config = parent_default_config
            log.warning(f"Flow config not found at {path_to_config}.")

        config = recursive_dictionary_update(config, overrides)
        return config

    @classmethod
    def instantiate_from_config(cls, config):
        kwargs = {"flow_config": config}
        return cls(**kwargs)

    @classmethod
    def instantiate_with_overrides(cls, overrides):
        config = cls.get_config(**overrides)
        return cls.instantiate_from_config(config)

    def set_up_flow_state(self):
        self.flow_state = {
            "history": FlowHistory()
        }

    def reset_flow_id(self):
        self.flow_run_id = create_unique_id()

    def reset(self, full_reset: bool):
        # ~~~ Delete all extraneous attributes ~~~
        for key, value in self.__dict__.items():
            if key not in self.KEYS_TO_IGNORE_WHEN_RESETTING_NAMESPACE:
                del self.__dict__[key]

        if full_reset:
            self.set_up_flow_state()  # resets the flow state
            self.reset_flow_id()

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
            # ToDo: This logs api_keys and everything in between. Should be fixed
            if key in self.flow_state:
                if value is None or value == self.flow_state[key]:
                    continue

            updates[key] = value
            self.flow_state[key] = copy.deepcopy(value)

        if updates:
            state_update_message = StateUpdateMessage(
                message_creator=self.flow_config['name'],
                parent_message_ids=parent_message_ids,
                flow_runner=self.flow_config['name'],
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
            # "config_param_updates": {k: self.__dict__[k]
            #                          for k in self.flow_config if self.flow_config[k] != self.__dict__[k]}
        }

    # def __setstate__(self, state):
    #     self.flow_config = copy.deepcopy(state["flow_config"])
    #     self.__set_config_params()
    #     self.flow_state = copy.deepcopy(state["flow_state"])
    #     for k, v in state["config_param_updates"].items():
    #         self.__setattr__(k, copy.deepcopy(v))
    #     self.flow_run_id = create_unique_id()

    def __repr__(self):
        # ~~~ This is the string that will be used by the hashing ~~~
        # ~~~ It keeps the config (self.flow_config) and the state (flow_state) ignoring some predefined keys ~~~
        flow_config_to_keep = set(self.flow_config.keys()) - set(self.KEYS_TO_IGNORE_HASH)
        config_hashing_params = {k: v for k, v in self.__dict__.items() if k in flow_config_to_keep}
        state_hashing_params = {k: v for k, v in self.flow_state.items() if k not in self.KEYS_TO_IGNORE_HASH}
        hash_dict = {"flow_config": config_hashing_params, "flow_state": state_hashing_params}
        # ToDo: Shouldn't composite flows include their subflows in the hashing, recursively?
        return repr(hash_dict)

    # def _clear(self):
    #     # ~~~ What should be kept ~~~
    #     state = self.__getstate__()
    #     flow_run_id = self.flow_run_id
    #
    #     # ~~~ Complete erasure ~~~
    #     self.__dict__ = {}
    #
    #     # ~~~ Restore what should be kept ~~~
    #     self.__setstate__(state)
    #     self.flow_run_id = flow_run_id

    def expected_inputs_given_state(self):
        return self.flow_config["expected_inputs"]

    def _log_message(self, message: Message):
        if self.flow_config["verbose"]:
            log.info(
                f"\n{colorama.Fore.RED} ~~~ Logging to history "
                f"[{self.flow_config['name']} -- {self.flow_run_id}] ~~~\n"
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
            error_message = f"The state of {self.flow_config['name']} [flow run ID: {self.flow_run_id}] does not contain" \
                            f"the following expected keys: {missing_keys}."

        return OutputMessage(
            message_creator=self.flow_config['name'],
            parent_message_ids=parent_message_ids,
            flow_runner=self.flow_config['name'],
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
            flow_runner=self.flow_config['name'],
            flow_run_id=self.flow_run_id,
            message_creator=self.flow_config['name'],
            target_flow_run_id=recipient_flow.flow_run_id,
            parent_message_ids=parent_message_ids,
            task_name=task_name,
            data=copy.deepcopy(task_data),
            expected_outputs=expected_outputs
        )

    def run(self, input_data: Dict[str, Any], expected_outputs: List[str]) -> Dict[str, Any]:
        raise NotImplementedError

    def set_up_api_keys(self, task_message):
        # ToDo: Deal with this in a better way
        if "api_key" in task_message.data:
            self.flow_state["api_key"] = task_message.data["api_key"]
            # We don't log it to history to not see it in the visualization
            # self._update_state(update_data={"api_key": str(api_key)})

        if getattr(self, "subflows", None):
            for subflow in self.subflows.values():
                subflow.set_up_api_keys(task_message=task_message)

        # ToDo: Isn't the api_key getting logged by the _log_message anyhow? We should fix that.

    def __call__(self, task_message: TaskMessage):
        self.set_up_api_keys(task_message=task_message)

        # ~~~ check and log input ~~~
        self._log_message(task_message)

        # ~~~ After the run is completed, the expected_outputs must be keys in the state ~~~
        expected_outputs = task_message.expected_outputs
        if expected_outputs is None:
            expected_outputs = self.flow_config["expected_outputs"]

        # ~~~ Execute the logic of the flow, it should populate state with expected_outputs ~~~
        outputs = self.run(input_data=task_message.data, expected_outputs=expected_outputs)

        # ~~~ Package output message ~~~
        output_message = self._package_output_message(
            outputs=outputs,
            expected_outputs=expected_outputs,
            parent_message_ids=[task_message.message_id]
        )

        self._post_call_hook()

        return output_message

    def _post_call_hook(self):
        # ~~~ destroying all attributes that are not flow_state or flow_config ~~~
        if self.flow_config['namespace_clearing_after_run']:
            self.reset(full_reset=False)


class AtomicFlow(Flow, ABC):

    def __init__(
            self,
            **kwargs
    ):
        if "flow_type" not in kwargs:
            kwargs["flow_type"] = "AtomicFlow"
        super().__init__(**kwargs)


class CompositeFlow(Flow, ABC):
    subflows: Union[Dict[str, Flow]]  # Dictionaries are ordered in Python 3.7+
    early_exit_key: str

    def __init__(
            self,
            **kwargs
    ):
        super().__init__(**kwargs)

    def _early_exit(self):
        early_exit_key = self.flow_config["early_exit_key"]
        if early_exit_key:
            if early_exit_key in self.flow_state:
                return bool(self.flow_state[early_exit_key])
            elif early_exit_key in self.__dict__:
                return bool(self.__dict__[early_exit_key])

        return False

    def _call_flow_from_state(
            self,
            flow: Flow,
            expected_outputs: list[str] = None,
            parent_message_ids: List[str] = None,
            search_class_namespace_for_inputs: bool = True
    ):
        expected_inputs = flow.expected_inputs_given_state()
        # ~~~ Prepare the call ~~~
        task_data = self._get_keys_from_state(
            keys=expected_inputs,
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

    @classmethod
    def _validate_parameters(cls, kwargs):
        # ToDo: Deal with this in a cleaner way (with less repetition)
        super()._validate_parameters(kwargs)

        if "subflows_config" not in kwargs["flow_config"]:
            raise KeyError("subflows_config must be specified in the flow_config.")

    @classmethod
    def _set_up_subflows(cls, config):
        subflows = {}  # Dictionaries are ordered in Python 3.7+
        subflows_config = config["subflows_config"]

        for subflow_config in subflows_config:
            flow_obj = hydra.utils.instantiate(subflow_config, _convert_="partial", _recursive_=False)
            subflows[flow_obj.flow_config["name"]] = flow_obj

        return subflows

    @classmethod
    def instantiate_from_config(cls, config):
        flow_config = copy.deepcopy(config)

        kwargs = {"flow_config": flow_config}
        kwargs["subflows"] = cls._set_up_subflows(flow_config)

        return cls(**kwargs)

    def set_up_flow_state(self):
        self.flow_state = {
            "history": FlowHistory()
        }

        for flow in self.subflows.values():
            flow.set_up_flow_state()

    def reset_flow_id(self, recursive: bool):
        self.flow_run_id = create_unique_id()

        if recursive:
            for flow in self.subflows.values():
                if isinstance(flow, CompositeFlow):
                    flow.reset_flow_id(recursive=True)
                else:
                    flow.flow_run_id = create_unique_id()

    def reset(self, full_reset: bool, recursive: bool):
        # ~~~ Delete all extraneous attributes ~~~
        for key, value in self.__dict__.items():
            if key not in self.KEYS_TO_IGNORE_WHEN_RESETTING_NAMESPACE:
                del self.__dict__[key]

        if full_reset:
            self.set_up_flow_state()  # resets the flow state
            self.reset_flow_id(recursive=False)

        # ~~~ Reset all subflows ~~~
        if recursive:
            for flow in self.subflows.values():
                if isinstance(flow, CompositeFlow):
                    flow.reset(full_reset=full_reset, recursive=True)
                else:
                    flow.reset(full_reset=full_reset)

    def _post_call_hook(self):
        # ~~~ destroying all attributes that are not flow_state or flow_config ~~~
        if self.flow_config['namespace_clearing_after_run']:
            self.reset(full_reset=False, recursive=False)

        for flow in self.subflows.values():
            flow._post_call_hook()
