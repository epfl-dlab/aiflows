"""

"""
import os
import sys
import copy
from abc import ABC
from typing import List, Dict, Any, Union, Optional

from omegaconf import OmegaConf
from ..utils import logging
from aiflows.history import FlowHistory
from aiflows.messages import (
    Message,
    InputMessage,
    UpdateMessage_Generic,
    UpdateMessage_NamespaceReset,
    UpdateMessage_FullReset,
    OutputMessage,
)
from aiflows.utils.general_helpers import recursive_dictionary_update, nested_keys_search, process_config_leafs, quick_load
from aiflows.utils.rich_utils import print_config_tree
from aiflows.flow_cache import FlowCache, CachingKey, CachingValue, CACHING_PARAMETERS
from ..utils.general_helpers import try_except_decorator
from ..utils.colink_helpers import get_next_update_message, create_subscriber
import colink as CL
import pickle
import hydra
import time
log = logging.get_logger(__name__)


class Flow(ABC):
    """
    Abstract class inherited by all Flows.

    :param flow_config: The configuration of the flow
    :type flow_config: Dict[str, Any]
    """

    # The required parameters that the user must provide in the config when instantiating a flow
    REQUIRED_KEYS_CONFIG = ["name", "description"]

    SUPPORTS_CACHING = False

    flow_config: Dict[str, Any]
    flow_state: Dict[str, Any]
    history: FlowHistory
    cl: CL.CoLink
    local_proxy_invocations: Dict[str,Any] = {}

    # Parameters that are given default values if not provided by the user
    __default_flow_config = {
        "colink_info": {
            "cl": 
                {
                    "_target_": "colink.CoLink",
                    "jwt": None,
                    "coreaddr": None
                },
            "remote_participant_id": None,
            "remote_participant_flow_queue": None,
            "load_incoming_states": False     
        },
        "private_keys": [],  # keys that will not be logged if they appear in a message
        "keys_to_ignore_for_hash_flow_config": ["name", "description", "api_keys", "api_information", "private_keys"],
        "keys_to_ignore_for_hash_flow_state": ["name", "description", "api_keys", "api_information", "private_keys"],
        "keys_to_ignore_for_hash_input_data": [],
        "clear_flow_namespace_on_run_end": True,  # whether to clear the flow namespace after each run
        "enable_cache": False,  # whether to enable cache for this flow
    }

    def __init__(
        self,
        flow_config: Dict[str, Any],
        cl: CL.CoLink = None,
    ):
        """
        __init__ should not be called directly be a user. Instead, use the classmethod `instantiate_from_config` or `instantiate_from_default_config`
        """
        self.flow_config = flow_config
        self.cache = FlowCache()
        
        self.cl = cl if cl is not None else self._set_up_colink()

        self.created_proxy_flow_entries = False
        # if self.cl is not None:
        #     self.cl.set_task_id(self.flow_config["task_id"])
        
        self._validate_flow_config(flow_config)
        
        
        self._determine_flow_type_and_set_up()
        
        self.set_up_flow_state()

        if log.getEffectiveLevel() == logging.DEBUG:
            log.debug(
                f"Flow {self.flow_config.get('name', 'unknown_name')} instantiated with the following parameters:"
            )
            print_config_tree(self.flow_config)
            
    def _make_queue_name(self,queue_name):
        queue_name_prefix = f"{self.flow_type}:{self.flow_config['name']}:{queue_name}"
        
        if queue_name_prefix not in Flow.local_proxy_invocations:
            Flow.local_proxy_invocations[queue_name_prefix] = 0
        
        Flow.local_proxy_invocations[queue_name_prefix] += 1
        
        queue_number = Flow.local_proxy_invocations[queue_name_prefix]

        return f"{queue_name_prefix}:{queue_number}"  
            
    def _determine_flow_type_and_set_up(self):
                
        if self.cl is None:
            self.flow_type = "LocalFlow"
        
        else:
            self.flow_type = "RemoteFlow"
            self.input_queue_name = self._make_queue_name(queue_name="input_queue")
            self.input_queue_subscriber = create_subscriber(self.cl,self.input_queue_name)
        
        colink_info = self.flow_config["colink_info"]
        
        if colink_info["remote_participant_id"] is not None:
            self.flow_type = "ProxyFlow"
            self.local_invocation = (
                CL.decode_jwt_without_validation(self.cl.jwt) == colink_info["remote_participant_id"]
            )
            
            #TODO: let's make this name always the same (so that the user doesn't have to specify it)
            self.remote_participant_flow_queue = colink_info["remote_participant_flow_queue"] 
            
            if self.local_invocation:
                self.response_queue_name = self._make_queue_name(queue_name="response_queue")
                                
                self.response_subscriber = create_subscriber(self.cl,self.response_queue_name)
            
            else:
                self.participants = [
                    CL.Participant(
                        user_id=CL.decode_jwt_without_validation(self.cl.jwt).user_id,
                        role="initiator",
                    ),
                    CL.Participant(
                        user_id= colink_info["remote_participant_id"],
                        role="target-flow",
                    ),
                ]
            

    @property
    def name(self):
        """Returns the name of the flow

        :return: The name of the flow
        :rtype: str
        """
        return self.flow_config["name"]

    @classmethod
    def instantiate_from_default_config(cls, **overrides: Optional[Dict[str, Any]]):
        """
        This method is called by the FlowLauncher to build the flow.

        :param overrides: The parameters to override in the default config
        :type overrides: Dict[str, Any], optional
        :return: The instantiated flow
        :rtype: aiflows.flow.Flow
        """
        if overrides is None:
            overrides = {}
        config = cls.get_config(**overrides)
                      
        return cls.instantiate_from_config(config)
    
    @classmethod
    def _validate_flow_config(cls, flow_config: Dict[str, Any]):
        """Validates the flow config to ensure that it contains all the required keys.

        :param flow_config: The flow config to validate
        :type flow_config: Dict[str, Any]
        :raises ValueError: If the flow config does not contain all the required keys
        """

                    
        if not hasattr(cls, "REQUIRED_KEYS_CONFIG"):
            raise ValueError("REQUIRED_KEYS_CONFIG should be defined for each Flow class.")

        for key in cls.REQUIRED_KEYS_CONFIG:
            if key not in flow_config:
                raise ValueError(f"{key} is a required parameter in the flow_config.")        
            
    @classmethod
    def get_config(cls, **overrides):
        """
        Returns the default config for the flow, with the overrides applied.
        The default implementation construct the default config by recursively merging the configs of the base classes.

        :param overrides: The parameters to override in the default config
        :type overrides: Dict[str, Any], optional
        :return: The default config with the overrides applied
        :rtype: Dict[str, Any]
        """
        if cls == Flow:
            return copy.deepcopy(cls.__default_flow_config)
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
            default_config = OmegaConf.to_container(OmegaConf.load(path_to_config), resolve=True)

            cls_parent_module = ".".join(cls.__module__.split(".")[:-1])

            process_config_leafs(
                default_config, lambda k, v: (cls_parent_module + v if k == "_target_" and v.startswith(".") else v)
            )

            config = recursive_dictionary_update(parent_default_config, default_config)
        elif hasattr(cls, f"_{cls.__name__}__default_flow_config"):
            # no yaml but __default_flow_config exists in class declaration
            config = recursive_dictionary_update(
                parent_default_config, copy.deepcopy(getattr(cls, f"_{cls.__name__}__default_flow_config"))
            )
        else:
            config = parent_default_config
            log.debug(f"Flow config not found at {path_to_config}.")
        # ~~~~ Apply the overrides ~~~~
        config = recursive_dictionary_update(config, overrides)

        # return cls.config_class(**overrides)
        return config
    
    def _set_up_colink(self):
        """ Sets up the colink flow object.
        
        :rtype: CL.CoLink
        """
        
        colink_info = self.flow_config["colink_info"]

        if colink_info["cl"]["coreaddr"] is not None and colink_info["cl"]["jwt"] is not None:
            return hydra.utils.instantiate(colink_info["cl"])
        
        else:
            return None
        

        
    @classmethod
    def instantiate_from_config(cls, config):
        """Instantiates the flow from the given config.

        :param config: The config to instantiate the flow from
        :type config: Dict[str, Any]
        :return: The instantiated flow
        :rtype: aiflows.flow.Flow
        """
        flow_config = copy.deepcopy(config)
        
        kwargs = {"flow_config": flow_config}
        
        return cls(**kwargs)

    @classmethod
    def instantiate_with_overrides(cls, overrides):
        """Instantiates the flow with the given overrides.

        :param overrides: The parameters to override in the default config
        :type overrides: Dict[str, Any], optional
        :return: The instantiated flow
        """
        config = cls.get_config(**overrides)
        return cls.instantiate_from_config(config)

    def set_up_flow_state(self):
        """Sets up the flow state. This method is called when the flow is instantiated, and when the flow is reset."""
        self.flow_state = {}
        self.history = FlowHistory()
        
    def get_flow_state(self):
        """Returns the flow state.

        :return: The flow state
        :rtype: Dict[str, Any]
        """
        return self.flow_state

    def reset(self, full_reset: bool, recursive: bool, src_flow: Optional[Union["Flow", str]] = "Launcher"):
        """
        Reset the flow state and history. If recursive is True, reset all subflows as well.

        :param full_reset:  If True, remove all data in flow_state. If False, keep the data in flow_state.
        :param recursive:
        :param src_flow:
        :return:
        """

        if isinstance(src_flow, Flow):
            src_flow = src_flow.flow_config["name"]

        if recursive and hasattr(self, "subflows"):
            for _, flow in self.subflows.items():
                flow.reset(full_reset=full_reset, recursive=True)

        if full_reset:
            message = UpdateMessage_FullReset(
                created_by=src_flow, updated_flow=self.flow_config["name"], keys_deleted_from_namespace=[]
            )
            self._log_message(message)
            self.set_up_flow_state()  # resets the flow state
        else:
            message = UpdateMessage_NamespaceReset(
                created_by=src_flow, updated_flow=self.flow_config["name"], keys_deleted_from_namespace=[]
            )
            self._log_message(message)

    def _get_from_state(self, key: str, default: Any = None):
        """Returns the value of the given key in the flow state. If the key does not exist, return the default value.

        :param key: The key to retrieve the value for
        :type key: str
        :param default: The default value to return if the key does not exist
        :type default: Any, optional
        :return: The value of the given key in the flow state
        :rtype: Any
        """
        return self.flow_state.get(key, default)

    def _state_update_dict(self, update_data: Union[Dict[str, Any], Message]):
        """
        Updates the flow state with the key-value pairs in a data dictionary (or message.data if a message is passed).

        :param update_data: The data dictionary to update the flow state with
        :type update_data: Union[Dict[str, Any], Message]
        """
        if isinstance(update_data, Message):
            update_data = update_data.data["output_data"]

        if len(update_data) == 0:
            raise ValueError(
                "The state_update_dict was called with an empty dictionary. If there is a justified "
                "reason to allow this, please replace the ValueError with a log.warning, and make a PR"
            )

        updates = {}
        for key, value in update_data.items():
            if key in self.flow_state:
                if value is None or value == self.flow_state[key]:
                    continue

            updates[key] = value
            self.flow_state[key] = copy.deepcopy(value)

        if len(updates) != 0:
            state_update_message = UpdateMessage_Generic(
                created_by=self.flow_config["name"],
                updated_flow=self.flow_config["name"],
                data=updates,
            )
            return self._log_message(state_update_message)

    def __getstate__(self, ignore_colink_info=False):
        """Used by the caching mechanism such that the flow can be returned to the same state using the cache"""
        flow_config = copy.deepcopy(self.flow_config)
        flow_state = copy.deepcopy(self.flow_state)
        if ignore_colink_info:
            flow_config.pop("colink_info")
        
        return {
            "flow_config": flow_config,
            "flow_state": flow_state,
        }

    def __setstate__(self, state,ignore_colink_info=False):
        """Used by the caching mechanism to skip computation that has already been done and stored in the cache"""
        if ignore_colink_info:
            colink_info = self.flow_config["colink_info"]
            assert colink_info is not None, "colink_info should never be None"
            state["flow_config"]["colink_info"] = colink_info
        
        self.__setflowstate__(state)
        self.__setflowconfig__(state)

    def __setflowstate__(self, state):
        """Used by the caching mechanism to skip computation that has already been done and stored in the cache"""
        self.flow_state = state["flow_state"]
        
    def __setflowconfig__(self, state):
        """Used by the caching mechanism to skip computation that has already been done and stored in the cache"""
        self.flow_config = state["flow_config"]

    def __repr__(self):
        """Generates the string that will be used by the hashing function"""
        # ~~~ This is the string that will be used by the hashing ~~~
        # ~~~ It keeps the config (self.flow_config) and the state (flow_state) ignoring some predefined keys ~~~
        config_hashing_params = {
            k: v
            for k, v in self.flow_config.items()
            if k not in self.flow_config["keys_to_ignore_for_hash_flow_config"]
        }
        state_hashing_params = {
            k: v for k, v in self.flow_state.items() if k not in self.flow_config["keys_to_ignore_for_hash_flow_state"]
        }
        hash_dict = {"flow_config": config_hashing_params, "flow_state": state_hashing_params}
        return repr(hash_dict)

    # def get_hash_string(self):
    #     raise NotImplementedError()

    def get_interface_description(self):
        """Returns the input and output interface description of the flow."""
        return {"input": self.flow_config["input_interface"], "output": self.flow_config["output_interface"]}

    def _log_message(self, message: Message):
        """Logs the given message to the history of the flow.

        :param message: The message to log
        :type message: Message
        :return: The message that was logged
        :rtype: Message
        """
        log.debug(message.to_string())
        return self.history.add_message(message)

    def _fetch_state_attributes_by_keys(self, keys: Union[List[str], None]):
        """Returns the values of the given keys in the flow state.

        :param keys: The keys to retrieve the values for
        :type keys: Union[List[str], None]
        :return: The values of the given keys in the flow state
        :rtype: Dict[str, Any]
        """
        data = {}

        if keys is None:
            # Return all available data
            for key in self.flow_state:
                data[key] = self.flow_state[key]

            return data

        for key in keys:
            value, found = nested_keys_search(self.flow_state, key)

            if found:
                data[key] = value
            else:
                raise KeyError(f"Key {key} not found in the flow state or the class namespace.")
        return data

    def _package_input_message(self, payload: Dict[str, Any], dst_flow: "Flow"):
        """Packages the given payload into an InputMessage.

        :param payload: The payload to package
        :type payload: Dict[str, Any]
        :param dst_flow: The destination flow
        :type dst_flow: Flow
        :return: The packaged input message
        :rtype: InputMessage
        """
        private_keys = dst_flow.flow_config["private_keys"]

        src_flow = self.flow_config["name"]
        if isinstance(dst_flow, Flow):
            dst_flow = dst_flow.flow_config["name"]

        assert (
            len(set(["src_flow", "dst_flow"]).intersection(set(payload.keys()))) == 0
        ), "The keys 'src_flow' and 'dst_flow' are special keys and cannot be used in the data dictionary"

        # ~~~ Create the message ~~~
        msg = InputMessage(
            data_dict=copy.deepcopy(payload),
            private_keys=private_keys,
            src_flow=src_flow,
            dst_flow=dst_flow,
            created_by=self.name,
        )
        return msg

    def _package_output_message(
        self, input_message: InputMessage, response: Dict[str, Any], raw_response: Dict[str, Any]
    ):
        """Packages the given response into an OutputMessage.

        :param input_message: The input message that was used to generate the response
        :type input_message: InputMessage
        :param response: The response to package
        :type response: Dict[str, Any]
        :param raw_response: The raw response to package
        :type raw_response: Dict[str, Any]
        :return: The packaged output message
        :rtype: OutputMessage
        """
        output_data = copy.deepcopy(response)

        return OutputMessage(
            created_by=self.flow_config["name"],
            src_flow=self.flow_config["name"],
            dst_flow=input_message.src_flow,
            output_data=output_data,
            raw_response=raw_response,
            input_message_id=input_message.message_id,
            history=self.history,
        )

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Runs the flow on the given input data. (Not implemented in the base class)

        :param input_data: The input data to run the flow on
        :type input_data: Dict[str, Any]
        :return: The response of the flow
        :rtype: Dict[str, Any]
        """
        raise NotImplementedError

    def __get_from_cache(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Gets the response from the cache if it exists. If it does not exist, runs the flow and caches the response.

        :param input_data: The input data to run the flow on
        :type input_data: Dict[str, Any]
        :return: The response of the flow
        :rtype: Dict[str, Any]
        """
        assert self.flow_config["enable_cache"] and CACHING_PARAMETERS.do_caching

        if not self.SUPPORTS_CACHING:
            raise Exception(
                f"Flow {self.flow_config['name']} does not support caching, but flow_config['enable_cache'] is True"
            )

        # ~~~ get the hash string ~~~
        keys_to_ignore_for_hash = self.flow_config["keys_to_ignore_for_hash_input_data"]
        input_data_to_hash = {k: v for k, v in input_data.items() if k not in keys_to_ignore_for_hash}
        cache_key_hash = CachingKey(self, input_data_to_hash, keys_to_ignore_for_hash).hash_string()
        # ~~~ get from cache ~~~
        response = None
        cached_value: CachingValue = self.cache.get(cache_key_hash)
        if cached_value is not None:
            # Retrieve output from cache
            response = cached_value.output_results

            # Restore the flow to the state it was in when the output was created
            self.__setstate__(cached_value.full_state)

            # Restore the history messages
            for message in cached_value.history_messages_created:
                message._reset_message_id()
                self._log_message(message)

            log.debug(
                f"Retrieved from cache: {self.__class__.__name__} "
                f"-- (input_data.keys()={list(input_data_to_hash.keys())}, "
                f"keys_to_ignore_for_hash={keys_to_ignore_for_hash})"
            )
            log.debug(f"Retrieved from cache: {str(cached_value)}")

        else:
            # Call the original function
            history_len_pre_execution = len(self.history)

            # Execute the call
            response = self.run(input_data)

            # Retrieve the messages created during the execution
            num_created_messages = len(self.history) - history_len_pre_execution
            new_history_messages = self.history.get_last_n_messages(num_created_messages)

            value_to_cache = CachingValue(
                output_results=response, full_state=self.__getstate__(), history_messages_created=new_history_messages
            )

            self.cache.set(cache_key_hash, value_to_cache)
            log.debug(f"Cached key: f{cache_key_hash}")

        return response
    
    def run_proxy(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Runs the flow in proxy mode.

        :param input_data: The input data to run the flow on
        :type input_data: Dict[str, Any]
        :return: The output data of the flow
        :rtype: Dict[str, Any]
        """
        
        log.debug("Running flow in proxy mode...")
        
        if "meta_data" not in input_data:
            input_data["colink_meta_data"] = {}
        
        if self.local_invocation:
            input_data["colink_meta_data"]["response_queue_name"] = self.response_queue_name
        input_data["colink_meta_data"]["state"] = self.__getstate__(ignore_colink_info=True)
        
        input_msg = InputMessage.build(
            data_dict=input_data,
            src_flow="SimpleProxyFlow",
            dst_flow=self.flow_config["colink_info"]["remote_participant_id"] + ":" + self.remote_participant_flow_queue,
        )
        
        self._log_message(input_msg)
             
        if self.local_invocation:
            
            self.cl.update_entry(self.remote_participant_flow_queue, pickle.dumps(input_msg))
            
            output_msg = get_next_update_message(self.response_subscriber)
            
        else:
            task_id = self.cl.run_task(
                "simple-invoke",
                pickle.dumps(self.remote_participant_flow_queue),
                self.participants,
                False,
            )
            
            self.cl.create_entry(
                f"simple-invoke-init:{self.remote_participant_flow_queue}:{task_id}:input_msg",
                pickle.dumps(input_msg),
            )
            
            output_msg = self.cl.read_or_wait(
                f"simple-invoke-init:{self.remote_participant_flow_queue}:{task_id}:output_msg",
            )
            
            output_msg = pickle.loads(output_msg)
        
        # assuming right now we are always sending the sate. Otherwise, this will fail
        state = output_msg.data.pop("colink_meta_data")["state"]
        self.__setstate__(state,ignore_colink_info=True)
        
        return output_msg.data
    
    def _run_method(self, input_data: Dict[str,Any]) -> Dict[str, Any]:
        """Runs the flow in local mode.

        :param input_message: The input message to run the flow on
        :type input_meassage: InputMessage
        :return: The output data of the flow
        :rtype: Dict[str, Any]
        """
        
        if self.flow_config["enable_cache"] and CACHING_PARAMETERS.do_caching:
            log.debug("call from cache")
            response = self.__get_from_cache(input_data)
            
        elif self.flow_type == "ProxyFlow":
            response = self.run_proxy(input_data)
        
        else:          
            response = self.run(input_data)
                
        return response
    
    def serve(self):
        """ Enables the flow to serve remote requests.  """
        
        assert self.flow_type != "LocalFlow", "You can't serve a local flow (it must have a CoLink instance)"
        log.info(f"Started Serving {self.flow_config['name']}. Input queue name is: {self.input_queue_name}")
        #doing while true right now (TODO: Consider having it set up with an event loop)
        while True:
            input_msg = get_next_update_message(self.input_queue_subscriber)
            
            colink_meta_data = input_msg.data.pop("colink_meta_data")
            
            #Note: atm, this is the queue of protocol operator. The proxyFlow's queue is being overwritten there
            response_queue_name = colink_meta_data["response_queue_name"] 
            
            #Some thoughts here: I think it's important to have decision of whether to load state or not
            # has to come from the flow itself (not the Proxy flow calling it)
            if self.flow_config["colink_info"]["load_incoming_states"]:
                #assuming state is ALWAYS sent
                self.__setstate__(colink_meta_data["state"],ignore_colink_info=True)
            
            
            
            output_msg = self(input_msg)
            
            if "meta_data" not in output_msg.data:
                output_msg.data["colink_meta_data"] = {}
        
            output_msg.data["colink_meta_data"]["state"] = self.__getstate__(ignore_colink_info=True)
            
            self.cl.update_entry(response_queue_name, pickle.dumps(output_msg))
        
    @try_except_decorator
    def __call__(self, input_message: InputMessage):
        """Calls the flow on the given input message.

        :param input_message: The input message to run the flow on
        :type input_message: InputMessage
        :param cl: The CoLink instance (only used for ProxyFlow, if none are set, the flow will run in local mode and the cl is ignored)
        :type cl: CL.CoLink
        :return: The output message of the flow
        :rtype: OutputMessage
        """
                
        # ~~~ check and log input ~~~
        self._log_message(input_message)

        # ~~~ Execute the logic of the flow ~~~
        
        response = self._run_method(input_message.data)

        # ~~~ Package output message ~~~
        output_message = self._package_output_message(
            input_message=input_message,
            response=response,
            raw_response=None,
        )

        self._post_call_hook()

        return output_message

    def _post_call_hook(self):
        """Removes all attributes from the namespace that are not in self.KEYS_TO_IGNORE_WHEN_RESETTING_NAMESPACE"""
        if self.flow_config["clear_flow_namespace_on_run_end"]:
            self.reset(full_reset=False, recursive=False, src_flow=self)

    def __str__(self):
        return self._to_string()

    def _to_string(self, indent_level=0):
        """Generates a string representation of the flow"""
        indent = "\t" * indent_level
        name = self.flow_config.get("name", "unnamed")
        description = self.flow_config.get("description", "no description")
        input_keys = self.flow_config.get("input_keys", "no input keys")
        output_keys = self.flow_config.get("output_keys", "no output keys")
        class_name = self.__class__.__name__

        entries = [
            f"{indent}Name: {name}",
            f"{indent}Class name: {class_name}",
            f"{indent}Type: {self.type()}",
            f"{indent}Description: {description}",
            f"{indent}Input keys: {input_keys}",
            f"{indent}Output keys: {output_keys}",
        ]
        return "\n".join(entries) + "\n"

    @classmethod
    def type(cls):
        raise NotImplementedError


    
    