import os
import sys
import copy

from abc import ABC
from typing import List, Dict, Any, Union, Optional, Callable

import colorama
import hydra
from omegaconf import OmegaConf

# ToDo: make imports relative
import flows
from flows import flow_verse
from ..utils import logging
from flows.data_transformations.abstract import DataTransformation
from flows.history import FlowHistory
from flows.messages import Message, InputMessage, UpdateMessage_Generic, \
    UpdateMessage_NamespaceReset, UpdateMessage_FullReset, \
    OutputMessage
from flows.utils.general_helpers import recursive_dictionary_update, validate_parameters, flatten_dict, unflatten_dict

log = logging.get_logger(__name__)


class Flow(ABC):
    KEYS_TO_IGNORE_WHEN_RESETTING_NAMESPACE = {"flow_config", "flow_state", "history", "input_message"}

    KEYS_TO_IGNORE_HASH = {"name", "description", "verbose"}
    SUPPORTS_CACHING = False

    REQUIRED_KEYS_CONFIG = ["name", "description", "verbose", "clear_flow_namespace_on_run_end", "output_keys"]
    REQUIRED_KEYS_KWARGS = ["flow_config", "input_data_transformations", "output_data_transformations"]

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

        if self.flow_config["verbose"]:
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
    def instantiate_from_default_config(cls, overrides: Optional[Dict[str, Any]] = None):
        """
        This method is called by the FlowLauncher to build the flow.
        """
        if overrides is None:
            overrides = {}

        config = cls.get_config(**overrides)

        return cls.instantiate_from_config(config)

    @classmethod
    def _validate_parameters(cls, kwargs):
        validate_parameters(cls, kwargs)

    @classmethod
    def get_config(cls, **overrides):
        """
        Returns the default config for the flow, with the overrides applied.

        The default implementation construct the default config by recursively merging the configs of the base classes.
        """
        if cls == Flow:
            config = {
                "input_data_transformations": [],
                "output_keys": [],
                "output_data_transformations": [],
                "verbose": True,
                "clear_flow_namespace_on_run_end": True,
                "keep_raw_response": True
            }
            return config
        elif cls == ABC:
            return {}
        elif cls == object:
            return {}

        # ~~~ Recursively retrieve and merge the configs of the base classes to construct the default config ~~~
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
            log.debug(f"Flow config not found at {path_to_config}.")

        # ~~~~ Apply the overrides ~~~~
        config = recursive_dictionary_update(config, overrides)
        return config

    @classmethod
    def _set_up_data_transformations(cls, data_transformation_configs):
        data_transformations = []
        if len(data_transformation_configs) > 0:
            for config in data_transformation_configs:
                if config["_target_"].startswith("."):
                    # assumption: cls is associated with relative data_transformation_configs
                    # for example, CF_Code and CF_Code.yaml should be in the same directory,
                    # and all _target_ in CF_Code.yaml should be relative
                    cls_parent_module = ".".join(cls.__module__.split(".")[:-1])
                    config["_target_"] = cls_parent_module + config["_target_"]
                data_transformations.append(hydra.utils.instantiate(config, _convert_="partial"))

        return data_transformations

    @classmethod
    def instantiate_from_config(cls, config):
        kwargs = {"flow_config": copy.deepcopy(config)}
        kwargs["input_data_transformations"] = cls._set_up_data_transformations(config["input_data_transformations"])
        kwargs["output_data_transformations"] = cls._set_up_data_transformations(config["output_data_transformations"])
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
        """
        Updates the flow state with the key-value pairs in a data dictionary (or message.data if a message is passed).

        """
        if isinstance(update_data, Message):
            update_data = update_data.data["output_data"]

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
        }

    def __setstate__(self, state):
        """Used by the caching mechanism to skip computation that has already been done and stored in the cache"""
        self.flow_config = state["flow_config"]
        self.flow_state = state["flow_state"]

    def __repr__(self):
        """Generates the string that will be used by the hashing function"""
        # ToDo: Document how this and the caching works (that all args should implement __repr__, should be applied only to atomic flows etc.)
        # ~~~ This is the string that will be used by the hashing ~~~
        # ~~~ It keeps the config (self.flow_config) and the state (flow_state) ignoring some predefined keys ~~~
        config_hashing_params = {k: v for k, v in self.flow_config.items() if k not in self.KEYS_TO_IGNORE_HASH}
        state_hashing_params = {k: v for k, v in self.flow_state.items() if k not in self.KEYS_TO_IGNORE_HASH}
        hash_dict = {"flow_config": config_hashing_params, "flow_state": state_hashing_params}
        return repr(hash_dict)

    # ToDo: Move the repr logic here
    # def get_hash_string(self):
    #     raise NotImplementedError()

    def get_input_keys(self, data: Optional[Dict[str, Any]] = None):
        """Returns the expected inputs for the flow given the current state and, optionally, the input data"""
        return self.flow_config["input_keys"]

    def get_output_keys(self, data: Optional[Dict[str, Any]] = None):
        """Returns the expected outputs for the flow given the current state and, optionally, the input data"""
        return self.flow_config["output_keys"]

    def _log_message(self, message: Message):
        log.debug(message.to_string())
        return self.history.add_message(message)

    def _fetch_state_attributes_by_keys(self,
                                        keys: Union[List[str], None],
                                        allow_class_attributes: bool = True):
        data = {}

        if keys is None:
            # Return all available data
            for key in self.flow_state:
                data[key] = self.flow_state[key]

            if allow_class_attributes:
                for key in self.__dict__:
                    if key in data:
                        log.warning(f"Data key {key} present in both in the flow state and the class namespace.")
                        continue
                    data[key] = self.__dict__[key]

            return data

        for key in keys:
            flat_flow_state = flatten_dict(self.flow_state)
            if key in flat_flow_state:
                data[key] = self.flow_state[key]
                continue

            if allow_class_attributes:
                if key in self.__dict__:
                    data[key] = self.__dict__[key]
        data = unflatten_dict(data)
        return data

    def package_input_message(
            self,
            data_dict: Dict[str, Any],
            src_flow: Optional[Union["Flow", str]] = "Launcher",
            input_keys: Optional[List[str]] = None,
            output_keys: Optional[List[str]] = None,
            api_keys: Optional[Dict[str, str]] = None,
            private_keys: Optional[List[str]] = None,  # Keys that should not be serialized or logged (e.g. api_keys)
            keys_to_ignore_for_hash: Optional[List[str]] = None,  # Keys that should not be hashed (e.g. api_keys)
    ):
        if isinstance(src_flow, Flow):
            src_flow = src_flow.flow_config["name"]
        dst_flow = self.flow_config["name"]

        # ~~~ Get the expected inputs and outputs ~~~
        data_dict = self._apply_data_transformations(data_dict,
                                                     self.input_data_transformations,
                                                     input_keys)
        if input_keys is None:
            input_keys = self.get_input_keys(data_dict)
        assert len(set(["src_flow", "dst_flow"]).intersection(set(input_keys))) == 0, \
            "The keys 'src_flow' and 'dst_flow' are special keys and cannot be used in the data dictionary"

        if output_keys is None:
            output_keys = self.get_output_keys(data_dict)

        # ~~~ Get the data payload ~~~
        packaged_data = {}
        for input_key in input_keys:
            if input_key not in data_dict:
                raise ValueError(f"Input data does not contain the expected key: `{input_key}`")

            packaged_data[input_key] = data_dict[input_key]

        # ~~~ Create the message ~~~
        # TODO(yeeef): dont pass through `api_keys` everywhere
        #              InputMessage contains `output_keys`, strange
        msg = InputMessage(
            created_by=self.flow_config['name'],
            data=copy.deepcopy(packaged_data),  # ToDo: Think whether deepcopy is necessary
            private_keys=private_keys,
            keys_to_ignore_for_hash=keys_to_ignore_for_hash,
            src_flow=src_flow,
            dst_flow=dst_flow,
            output_keys=output_keys,
            api_keys=api_keys,
        )
        return msg

    def _apply_data_transformations(self,
                                    data_dict: Dict,
                                    data_transformations: List[DataTransformation],
                                    keys: List[str]):
        data_transforms_to_apply = []
        for data_transform in data_transformations:
            if data_transform.output_key is None or data_transform.output_key in keys:
                data_transforms_to_apply.append(data_transform)

        for data_transform in data_transforms_to_apply:
            data_dict = data_transform(data_dict)

        return data_dict

    def _package_output_message(
            self,
            input_message: InputMessage,
            response: Any,
    ):
        output_data = {"raw_response": response}

        # ~~~ Flatten the output data ~~~
        output_data = flatten_dict(output_data)

        # ~~~ Apply output transformations ~~~
        output_keys = input_message.data["output_keys"]
        output_data = self._apply_data_transformations(output_data,
                                                       self.output_data_transformations,
                                                       output_keys)

        # ~~~ Check that all expected keys are present ~~~
        missing_keys = []
        for expected_key in input_message.data["output_keys"]:
            if expected_key not in output_data:
                missing_keys.append(expected_key)
                continue

        # ~~~ Unflatten the output data ~~~
        output_data = unflatten_dict(output_data)

        if not self.flow_config["keep_raw_response"]:
            del output_data["raw_response"]
            log.warning("The raw response was not logged.")

        if len(output_data) == 0:
            raise Exception(f"The output dictionary is empty. "
                            f"None of the expected outputs: `{str(output_keys)}` were found.")

        if self.flow_config["verbose"] and len(missing_keys) != 0:
            flow_name = self.flow_config['name']
            log.warning(f"[{flow_name}] Missing keys: `{str(missing_keys)}`. "
                        f"Available outputs are: `{str(list(output_data.keys()))}`")

        return OutputMessage(
            created_by=self.flow_config['name'],
            src_flow=self.flow_config['name'],
            dst_flow=input_message.src_flow,
            output_keys=input_message.data["output_keys"],
            output_data=output_data,
            input_message_id=input_message.message_id,
            missing_output_keys=missing_keys,
            history=self.history,
        )

    # TODO(yeeef): `output_keys` is in input_message.data, which is an implicit assumption
    #              `raw_response` is in outputs, which is an implicit assumption
    def run(self,
            input_data: Dict[str, Any],
            private_keys: Optional[List[str]] = [],
            keys_to_ignore_for_hash: Optional[List[str]] = []) -> Dict[str, Any]:
        raise NotImplementedError

    def __call__(self, input_message: InputMessage):
        self.input_message = input_message

        # ~~~ check and log input ~~~
        self._log_message(input_message)

        # ~~~ Execute the logic of the flow, it should populate state with output_keys ~~~
        assert "output_keys" in input_message.data and \
               (len(input_message.data["output_keys"]) > 0 or self.flow_config["keep_raw_response"]), \
            "The input message must contain the key 'output_keys' with at least one expected output"
        response = self.run(input_data=input_message.data,
                            private_keys=input_message.private_keys,
                            keys_to_ignore_for_hash=input_message.keys_to_ignore_for_hash)

        # ~~~ Package output message ~~~
        output_message = self._package_output_message(
            input_message=input_message,
            response=response,
        )

        self._post_call_hook()

        return output_message

    def _post_call_hook(self):
        """Removes all attributes from the namespace that are not in self.KEYS_TO_IGNORE_WHEN_RESETTING_NAMESPACE"""
        if self.flow_config['clear_flow_namespace_on_run_end']:
            self.reset(full_reset=False, recursive=False)

    def __str__(self):
        return self._to_string()
    def _to_string(self, indent_level=0):
        """Generates a string representation of the flow"""
        indent = "\t" * indent_level
        name = self.flow_config["name"]
        description = self.flow_config["description"]
        input_keys = self.flow_config["input_keys"]
        output_keys = self.flow_config["output_keys"]
        class_name = self.__class__.__name__

        entries = [
            f"{indent}Name: {name}",
            f"{indent}Class name: {class_name}",
            f"{indent}Description: {description}",
            f"{indent}Input keys: {input_keys}",
            f"{indent}Output keys: {output_keys}",
        ]
        return "\n".join(entries) + "\n"




class AtomicFlow(Flow, ABC):

    def __init__(
            self,
            **kwargs
    ):
        super().__init__(**kwargs)


class CompositeFlow(Flow, ABC):
    REQUIRED_KEYS_CONFIG = ["subflows_config"]
    REQUIRED_KEYS_KWARGS = ["flow_config", "subflows"]

    subflows: Dict[str, Flow]  # Dictionaries are ordered in Python 3.7+

    def __init__(
            self,
            **kwargs
    ):
        super().__init__(**kwargs)

    def _early_exit(self):
        early_exit_key = self.flow_config.get("early_exit_key", None)
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
        """A helper function that calls a given flow by extracting the input data from the state of the current flow."""
        # ~~~ Prepare the data for the call ~~~
        api_keys = getattr(self, 'api_keys', None)
        input_data = self._fetch_state_attributes_by_keys(
            keys=None,
            allow_class_attributes=search_class_namespace_for_inputs
        )
        input_message = flow_to_call.package_input_message(data_dict=input_data,
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
    def _set_up_subflows(cls, config):
        subflows = {}  # Dictionaries are ordered in Python 3.7+
        subflows_config = config["subflows_config"]

        for subflow_config in subflows_config:
            # Let's use hydra for now
            # subflow_config["_target_"] = flow_verse.loading.DEFAULT_FLOW_MODULE_FOLDER + "." + subflow_config.pop("class") + ".instantiate_from_default_config"
            flow_obj = hydra.utils.instantiate(subflow_config, _convert_="partial", _recursive_=False)
            subflows[flow_obj.flow_config["name"]] = flow_obj

        return subflows

    @classmethod
    def instantiate_from_config(cls, config):
        flow_config = copy.deepcopy(config)

        kwargs = {"flow_config": copy.deepcopy(flow_config)}
        kwargs["subflows"] = cls._set_up_subflows(flow_config)
        kwargs["input_data_transformations"] = cls._set_up_data_transformations(config["input_data_transformations"])
        kwargs["output_data_transformations"] = cls._set_up_data_transformations(config["output_data_transformations"])

        return cls(**kwargs)

    def __str__(self):
        return self._to_string()

    def _to_string(self, indent_level=0):
        """Generates a string representation of the flow"""
        indent = "\t" * indent_level
        name = self.flow_config["name"]
        description = self.flow_config["description"]
        input_keys = self.flow_config["input_keys"]
        output_keys = self.flow_config["output_keys"]
        class_name = self.__class__.__name__
        subflows_repr = "\n".join([f"{subflow._to_string(indent_level=indent_level + 1)}" for subflow in self.subflows.values()])

        entries = [
            f"{indent}Name: {name}",
            f"{indent}Class name: {class_name}",
            f"{indent}Description: {description}",
            f"{indent}Input keys: {input_keys}",
            f"{indent}Output keys: {output_keys}",
            f"{indent}Subflows:",
            f"{subflows_repr}"
        ]
        return "\n".join(entries)
