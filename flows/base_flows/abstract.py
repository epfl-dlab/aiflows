import os
import sys
import copy

from abc import ABC
from typing import List, Dict, Any, Union, Optional

import colorama
import hydra
from omegaconf import OmegaConf

# ToDo: make imports relative
import flows
from flows import utils
from flows.history import FlowHistory
from flows.messages import Message, InputMessage, UpdateMessage_Generic, \
    UpdateMessage_NamespaceReset, UpdateMessage_FullReset, \
    OutputMessage
from flows.utils.general_helpers import recursive_dictionary_update, validate_parameters

log = utils.get_pylogger(__name__)


class Flow(ABC):
    KEYS_TO_IGNORE_WHEN_RESETTING_NAMESPACE = set(["flow_config", "flow_state", "history"])

    KEYS_TO_IGNORE_HASH = set(["name", "description", "verbose"])
    SUPPORTS_CACHING = False

    REQUIRED_KEYS_CONFIG = ["name", "description"]
    REQUIRED_KEYS_KWARGS = ["flow_config"]

    flow_config: Dict[str, Any]
    flow_state: Dict[str, Any]
    history: FlowHistory

    def __init__(
            self,
            **kwargs_passed_to_the_constructor
    ):
        self.flow_state = None
        self.flow_config = None
        self.history = None

        self._validate_parameters(kwargs_passed_to_the_constructor)
        self._extend_keys_to_ignore_when_resetting_namespace(list(kwargs_passed_to_the_constructor.keys()))
        self.__set_namespace_params(kwargs_passed_to_the_constructor)

        if self.flow_config.get("verbose", True):
            # ToDo: print the flow config with Rich
            pass

        self.set_up_flow_state()

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
    def _validate_parameters(cls, kwargs):
        validate_parameters(cls, kwargs)

    @classmethod
    def get_config(cls, **overrides):
        if cls == Flow:
            config = {
                "expected_outputs": [],
                "verbose": True,
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
        kwargs = {"flow_config": copy.deepcopy(config)}
        return cls(**kwargs)

    @classmethod
    def instantiate_with_overrides(cls, overrides):
        config = cls.get_config(**overrides)
        return cls.instantiate_from_config(config)

    def set_up_flow_state(self):
        self.flow_state = {}
        self.history = FlowHistory()

    def reset(self, full_reset: bool, recursive: bool):
        # ~~~ Delete all extraneous attributes ~~~
        keys_deleted_from_namespace = []
        for key, value in list(self.__dict__.items()):
            if key not in self.KEYS_TO_IGNORE_WHEN_RESETTING_NAMESPACE:
                del self.__dict__[key]
                keys_deleted_from_namespace.append(key)

        if recursive and hasattr(self, "subflows"):
            for flow in self.subflows.values():
                flow.reset(full_reset=full_reset, recursive=True)

        if full_reset:
            message = UpdateMessage_FullReset(
                created_by=self.flow_config['name'],  # ToDo: Update this to the flow from which the reset was called
                updated_flow=self.flow_config["name"],
                keys_deleted_from_namespace=keys_deleted_from_namespace
            )
            self._log_message(message)
            self.set_up_flow_state()  # resets the flow state
        else:
            message = UpdateMessage_NamespaceReset(
                created_by=self.flow_config['name'],  # ToDo: Update this to the flow from which the reset was called
                updated_flow=self.flow_config["name"],
                keys_deleted_from_namespace=keys_deleted_from_namespace
            )
            self._log_message(message)

    def _state_update_dict(self, update_data: Union[Dict[str, Any], Message]):
        if isinstance(update_data, Message):
            update_data = update_data.data["outputs"]

        if len(update_data) == 0:  # ToDo: Should we allow empty state updates, with a warning? When would this happen?
            raise ValueError("The state_update_dict was called with an empty dictionary.")

        updates = {}
        for key, value in update_data.items():
            if key in self.flow_state:
                if value is None or value == self.flow_state[key]:
                    continue

            updates[key] = value
            self.flow_state[key] = copy.deepcopy(value)

        if len(updates) != 0:
            state_update_message = UpdateMessage_Generic(
                created_by=self.flow_config['name'],
                updated_flow=self.flow_config["name"],
                data=updates,
            )
            return self._log_message(state_update_message)

    def __getstate__(self):
        """Used by the caching mechanism such that the flow can be returned to the same state using the cache"""
        return {
            "flow_config": self.flow_config,
            "flow_state": self.flow_state,
            "history": self.history,
        }

    def __setstate__(self, state):
        """Used by the caching mechanism to skip computation that has already been done and stored in the cache"""
        self.flow_config = state["flow_config"]
        self.flow_state = state["flow_state"]
        # ToDo: Make sure that the below is soft copy, by updating the __getstate__ of the history
        self.history = state["history"]


    def __repr__(self):
        """Generates the string that will be used by the hashing function"""
        # ToDo: Document how this and the caching works (that all args should implement __repr__, should be applied only to atomic flows etc.)
        # ~~~ This is the string that will be used by the hashing ~~~
        # ~~~ It keeps the config (self.flow_config) and the state (flow_state) ignoring some predefined keys ~~~
        config_hashing_params = {k: v for k, v in self.flow_config.items() if k not in self.KEYS_TO_IGNORE_HASH}
        state_hashing_params = {k: v for k, v in self.flow_state.items() if k not in self.KEYS_TO_IGNORE_HASH}
        hash_dict = {"flow_config": config_hashing_params, "flow_state": state_hashing_params}
        return repr(hash_dict)

    def get_expected_inputs(self, data: Optional[Dict[str, Any]] = None):
        """Returns the expected inputs for the flow given the current state and, optionally, the input data"""
        return self.flow_config["expected_inputs"]

    def get_expected_outputs(self, data: Optional[Dict[str, Any]] = None):
        """Returns the expected outputs for the flow given the current state and, optionally, the input data"""
        return self.flow_config["expected_outputs"]

    def _log_message(self, message: Message):
        if self.flow_config["verbose"]:
            log.info(message.to_string())
        return self.history.add_message(message)

    def _get_keys_from_state(self, keys: List[str], allow_class_namespace: bool = True):
        data = {}

        if keys is None:
            # Return all available data
            for key in self.flow_state:
                data[key] = self.flow_state[key]

            if allow_class_namespace:
                for key in self.__dict__:
                    if key in data:
                        log.warning(f"Data key {key} present in both in the flow state and the class namespace.")
                        continue
                    data[key] = self.__dict__[key]

            return data

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
            input_message: InputMessage,
            outputs: Dict[str, Any],
    ):
        missing_keys = []
        for expected_key in input_message.data["expected_outputs"]:
            if expected_key not in outputs:
                missing_keys.append(expected_key)
                continue

        return OutputMessage(
            created_by=self.flow_config['name'],
            src_flow=self.flow_config['name'],
            dst_flow=input_message.data["src_flow"],
            expected_outputs=input_message.data["expected_outputs"],
            outputs=outputs,
            missing_expected_outputs=missing_keys,
            history=self.history,
        )

    def package_input_message(
            self,
            data: Dict[str, Any],
            src_flow: Optional[Union["Flow", str]] = "Launcher",
            expected_inputs: Optional[List[str]] = None,
            expected_outputs: Optional[List[str]] = None,
            api_keys: Optional[List[str]] = None,
            private_keys: Optional[List[str]] = None,  # Keys that should not be serialized or logged (e.g. api_keys)
            keys_to_ignore_for_hash: Optional[List[str]] = None,  # Keys that should not be hashed (e.g. api_keys)
    ):
        if isinstance(src_flow, Flow):
            src_flow = src_flow.flow_config["name"]
        dst_flow = self.flow_config["name"]

        # ~~~ Get the expected inputs and outputs ~~~
        if expected_inputs is None:
            expected_inputs = self.get_expected_inputs(data)
        assert len(set(["src_flow", "dst_flow"]).intersection(set(expected_inputs))) == 0, \
            "The keys 'src_flow' and 'dst_flow' are special keys and cannot be used in the data dictionary"

        if expected_outputs is None:
            expected_outputs = self.get_expected_outputs(data)
        if "raw_response" not in expected_outputs:  # Corresponds to the raw unprocessed response
            expected_outputs.append("raw_response")

        # ~~~ Get the data payload ~~~
        packaged_data = {}
        for input_key in expected_inputs:
            if input_key not in data:
                raise ValueError(f"Input data does not contain the expected key: {input_key}")

            packaged_data[input_key] = data[input_key]

        # ~~~ Create the message ~~~
        msg = InputMessage(
            created_by=self.flow_config['name'],
            data=copy.deepcopy(packaged_data),  # ToDo: Think whether deepcopy is necessary
            private_keys=private_keys,
            keys_to_ignore_for_hash=keys_to_ignore_for_hash,
            src_flow=src_flow,
            dst_flow=dst_flow,
            expected_outputs=expected_outputs,
            api_keys=api_keys,
        )
        return msg

    def run(self,
            input_data: Dict[str, Any],
            private_keys: Optional[List[str]] = [],
            keys_to_ignore_for_hash: Optional[List[str]] = []) -> Dict[str, Any]:
        raise NotImplementedError

    def __call__(self, input_message: InputMessage):
        # ~~~ check and log input ~~~
        self._log_message(input_message)

        # ~~~ Execute the logic of the flow, it should populate state with expected_outputs ~~~
        assert "expected_outputs" in input_message.data and len(input_message.data["expected_outputs"]) > 0, \
            "The input message must contain the key 'expected_outputs' with at least one expected output"
        outputs = self.run(input_data=input_message.data,
                           private_keys=input_message.private_keys,
                           keys_to_ignore_for_hash=input_message.keys_to_ignore_for_hash)

        # ~~~ Package output message ~~~
        output_message = self._package_output_message(
            input_message=input_message,
            outputs=outputs,
        )

        self._post_call_hook()

        return output_message

    def _post_call_hook(self):
        """Removes all attributes from the namespace that are not in self.KEYS_TO_IGNORE_WHEN_RESETTING_NAMESPACE"""
        if self.flow_config['namespace_clearing_after_run']:
            self.reset(full_reset=False, recursive=False)


class AtomicFlow(Flow, ABC):

    def __init__(
            self,
            **kwargs
    ):
        super().__init__(**kwargs)


class CompositeFlow(Flow, ABC):
    REQUIRED_KEYS_CONFIG = ["early_exit_key", "subflows_config"]
    REQUIRED_KEYS_KWARGS = ["flow_config", "subflows"]

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
            flow_to_call: Flow,
            private_keys,
            keys_to_ignore_for_hash,
            search_class_namespace_for_inputs: bool = True
    ):
        # ~~~ Prepare the data for the call ~~~
        api_keys = getattr(self, 'api_keys', None)
        input_data = self._get_keys_from_state(
            keys=None,
            allow_class_namespace=search_class_namespace_for_inputs
        )
        input_message = flow_to_call.package_input_message(data=input_data,
                                                           src_flow=self,
                                                           private_keys=private_keys,
                                                           keys_to_ignore_for_hash=keys_to_ignore_for_hash,
                                                           api_keys=api_keys)

        # ~~~ Execute the call ~~~
        output_message = flow_to_call(input_message)

        # ~~~ Logs the output message to history ~~~
        self._log_message(output_message)

        return output_message

    @classmethod
    def _validate_parameters(cls, kwargs):
        validate_parameters(cls, kwargs)

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

        kwargs = {"flow_config": copy.deepcopy(flow_config)}
        kwargs["subflows"] = cls._set_up_subflows(flow_config)

        return cls(**kwargs)
