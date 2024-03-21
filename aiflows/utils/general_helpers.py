import collections
from pathlib import Path
from typing import List, Any, Tuple, Dict, Callable, Union
import uuid
import time
import os
import ast
import json
import jsonlines
import gzip
import importlib
from omegaconf import OmegaConf
from aiflows.backends.api_info import ApiInfo

# from litellm.utils import function_to_dict
from aiflows.utils import logging
import base64

log = logging.get_logger(__name__)


def validate_flow_config(cls, flow_config):
    """Validates the flow config.

    :param cls: The class to validate the flow config for
    :type cls: class
    :param flow_config: The flow config to validate
    :type flow_config: Dict[str, Any]
    :raises ValueError: If the flow config is invalid
    """
    if cls.__name__ != "Flow":
        cls.__base__._validate_flow_config(flow_config)

    if not hasattr(cls, "REQUIRED_KEYS_CONFIG"):
        raise ValueError("REQUIRED_KEYS_CONFIG should be defined for each Flow class.")

    for key in cls.REQUIRED_KEYS_CONFIG:
        if key not in flow_config:
            raise ValueError(f"{key} is a required parameter in the flow_config.")


def flatten_dict(d, parent_key="", sep="."):
    """Flattens a dictionary.

    :param d: The dictionary to flatten
    :type d: Dict[str, Any]
    :param parent_key: The parent key to use, defaults to ''
    :type parent_key: str, optional
    :param sep: The separator to use, defaults to '.'
    :type sep: str, optional
    :return: The flattened dictionary
    :rtype: Dict[str, Any]
    """
    items = []
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


# Function to unflatten dictionary
def unflatten_dict(d, sep="."):
    """Unflattens a dictionary.

    :param d: The dictionary to unflatten
    :type d: Dict[str, Any]
    :param sep: The separator to use, defaults to '.'
    :type sep: str, optional
    :return: The unflattened dictionary
    :rtype: Dict[str, Any]
    """
    result_dict = dict()
    for k, v in d.items():
        parts = k.split(sep)
        d = result_dict
        for part in parts[:-1]:
            if part not in d:
                d[part] = dict()
            d = d[part]
        d[parts[-1]] = v
    return result_dict


def nested_keys_pop(data_dict: dict, nested_key: str) -> Any:
    """
    Pop a nested key in a dictionary.

    :param data_dict: The dictionary to pop from.
    :type data_dict: dict
    :param nested_key: The nested key to pop, in the format "key1.key2.key3".
    :type nested_key: str
    :return: The value of the popped key.
    :rtype: Any
    """
    keys = nested_key.split(".")

    d = data_dict
    for key in keys[:-1]:
        if key not in d:
            return
        d = d[key]

    return d.pop(keys[-1], None)


def nested_keys_update(data_dict: dict, nested_key: str, value: Any) -> None:
    """
    Update the value of a nested key in a dictionary.

    :param data_dict: The dictionary to update.
    :type data_dict: dict
    :param nested_key: The nested key to update, in the format "key1.key2.key3".
    :type nested_key: str
    :param value: The new value to set for the nested key.
    :type value: Any
    """
    keys = nested_key.split(".")

    d = data_dict
    for key in keys[:-1]:
        if key not in d:
            d[key] = dict()
        d = d[key]

    d[keys[-1]] = value


def nested_keys_search(search_dict, nested_key) -> Tuple[Any, bool]:
    """
    Searches for a nested key in a dictionary using a composite key string.

    :param search_dict: The dictionary to search in.
    :type search_dict: dict
    :param nested_key: The composite key string to search for.
    :type nested_key: str
    :return: A tuple containing the value of the nested key and a boolean indicating if the key was found.
    :rtype: Tuple[Any, bool]
    """

    def do_search(search_dict, keys):
        if len(keys) == 1:
            if keys[0] in search_dict:
                return search_dict[keys[0]], True
            else:
                return None, False

        if keys[0] in search_dict:
            return do_search(search_dict[keys[0]], keys[1:])
        else:
            return None, False

    return do_search(search_dict, nested_key.split("."))


def process_config_leafs(config: Union[Dict, List], leaf_processor: Callable[[Tuple[Any, Any]], Any]):
    """Processes the leafs of a config dictionary or list.

    :param config: The config to process
    :type config: Union[Dict, List]
    :param leaf_processor: The leaf processor to use
    :type leaf_processor: Callable[[Tuple[Any, Any]], Any]
    """
    if not config:
        return

    if isinstance(config, dict):
        for k, v in config.items():
            if not isinstance(v, dict) and not isinstance(v, list):
                config[k] = leaf_processor(k, v)
            else:
                process_config_leafs(v, leaf_processor)
    elif isinstance(config, list):
        for item in config:
            if isinstance(item, dict) or isinstance(item, list):
                process_config_leafs(item, leaf_processor)
            else:
                pass
    else:
        assert False


def read_jsonlines(path_to_file):
    """Reads a jsonlines file and returns a list of dictionaries.

    :param path_to_file: The path to the jsonlines file
    :type path_to_file: str
    :return: A list of dictionaries
    :rtype: List[Dict[str, Any]]
    """
    with open(path_to_file, "r") as f:
        json_reader = jsonlines.Reader(f)
        return list(json_reader)


def write_jsonlines(path_to_file, data, mode="w"):
    """Writes a list of dictionaries to a jsonlines file.

    :param path_to_file: The path to the jsonlines file
    :type path_to_file: str
    :param data: The data to write
    :type data: List[Dict[str, Any]]
    :param mode: The mode to use, defaults to "w"
    :type mode: str, optional
    """
    with jsonlines.open(path_to_file, mode) as writer:
        writer.write_all(data)


def write_gzipped_jsonlines(path_to_file, data, mode="w"):
    """Writes a list of dictionaries to a gzipped jsonlines file.

    :param path_to_file: The path to the gzipped jsonlines file
    :type path_to_file: str
    :param data: The data to write
    :type data: List[Dict[str, Any]]
    :param mode: The mode to use, defaults to "w"
    :type mode: str, optional
    """
    with gzip.open(path_to_file, mode) as fp:
        json_writer = jsonlines.Writer(fp)
        json_writer.write_all(data)


def read_gzipped_jsonlines(path_to_file):
    """Reads a gzipped jsonlines file and returns a list of dictionaries.

    :param path_to_file: The path to the gzipped jsonlines file
    :type path_to_file: str
    :return: A list of dictionaries
    :rtype: List[Dict[str, Any]]
    """
    with gzip.open(path_to_file, "r") as fp:
        json_reader = jsonlines.Reader(fp)
        return list(json_reader)


def create_unique_id(existing_ids: List[str] = None):
    """creates a unique id

    :param existing_ids: A list of existing ids to check against, defaults to None
    :type existing_ids: List[str], optional
    :return: A unique id
    :rtype: str
    """
    if existing_ids is None:
        existing_ids = set()

    while True:
        unique_id = str(uuid.uuid4())
        if unique_id not in existing_ids:
            return unique_id


def get_current_datetime_ns():
    """Returns the current datetime in nanoseconds.

    :return: The current datetime in nanoseconds
    :rtype: int
    """
    time_of_creation_ns = time.time_ns()

    # Convert nanoseconds to seconds and store as a time.struct_time object
    time_of_creation_struct = time.gmtime(time_of_creation_ns // 1000000000)

    # Format the time.struct_time object into a human-readable string
    formatted_time_of_creation = time.strftime("%Y-%m-%d %H:%M:%S", time_of_creation_struct)

    # Append the nanoseconds to the human-readable string
    formatted_time_of_creation += f".{time_of_creation_ns % 1000000000:09d}"

    return formatted_time_of_creation


def get_predictions_dir_path(output_dir, create_if_not_exists=True):
    """Returns the path to the predictions folder.

    :param output_dir: The output directory
    :type output_dir: str
    :param create_if_not_exists: Whether to create the folder if it does not exist, defaults to True
    :type create_if_not_exists: bool, optional
    :return: The path to the predictions folder
    :rtype: str
    """
    if output_dir is not None:
        predictions_folder = os.path.join(output_dir, "predictions")
    else:
        predictions_folder = "predictions"

    if create_if_not_exists:
        Path(predictions_folder).mkdir(parents=True, exist_ok=True)

    return predictions_folder


def write_outputs(path_to_output_file, summary, mode):
    """Writes the summary to a jsonlines file.

    :param path_to_output_file: The path to the output file
    :type path_to_output_file: str
    :param summary: The summary to write
    :type summary: List[Dict[str, Any]]
    :param mode: The mode to use
    :type mode: str
    """

    def to_dict_serializer(obj):
        """JSON serialized for object that have the to_dict method implemented"""
        if hasattr(obj, "to_dict"):
            return obj.to_dict()
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

    def to_dict_dumps(obj):
        # return json.dumps(obj, default=to_dict_serializer, indent=4) breaks the jsonlines reader (see below)
        # ToDo: If you update this, make sure that the reader is consistent with the writer
        # ToDo: Also, we should gzip the output file because it has a lot of redundancy
        return json.dumps(obj, default=to_dict_serializer)

    with open(path_to_output_file, mode) as fp:
        json_writer = jsonlines.Writer(fp, dumps=to_dict_dumps)
        json_writer.write_all(summary)


def read_outputs(outputs_dir):
    """Reads the outputs from a jsonlines file.

    :param outputs_dir: The directory containing the output files
    :type outputs_dir: str
    :return: The outputs
    :rtype: List[Dict[str, Any]]
    """
    items_dict = dict()

    for filename in os.listdir(outputs_dir):
        if not filename.endswith(".jsonl"):
            continue

        input_file_path = os.path.join(outputs_dir, filename)
        with open(input_file_path, "r+") as fp:
            # reader = jsonlines.Reader(fp)
            # for element in reader:
            for idx, line in enumerate(fp):
                try:
                    element = json.loads(line)
                except json.decoder.JSONDecodeError:
                    log.error(f"Failed to decode line {idx} in file {input_file_path}")
                    continue
                assert "id" in element
                # due to potentially non-even splits across processes, inference with ddp might result in duplicates
                # (i.e., the same datapoint might have been seen multiple times)
                # however we will always consider only one prediction (the last one)
                items_dict[element["id"]] = element

    items = [items_dict[_id] for _id in sorted(items_dict.keys())]
    return items


def recursive_dictionary_update(d, u):
    """Performs a recursive update of the values in dictionary d with the values of dictionary u

    :param d: The dictionary to update
    :type d: Dict[str, Any]
    :param u: The dictionary to update with
    :type u: Dict[str, Any]
    :return: The updated dictionary
    """
    if d is None:
        d = {}
    for k, v in u.items():
        if isinstance(v, collections.abc.Mapping) and isinstance(d.get(k, {}), collections.abc.Mapping):
            d[k] = recursive_dictionary_update(d.get(k, {}), v)
        else:
            d[k] = v
    return d


def log_suggest_help():
    """Logs a message suggesting to get help or provide feedback on github."""
    red = "\033[31m"
    reset = "\x1b[0m"
    green = "\033[32m"
    bold = "\033[1m"
    github_issues_link = "https://github.com/epfl-dlab/aiflows/issues \n\n"
    message = " \n\nFor feedback or to get help:  "
    log.info(bold + red + message + reset + bold + green + github_issues_link)


def exception_handler(e):
    """Handles an exception.

    :param e: The exception to handle
    :type e: Exception
    """
    log_suggest_help()
    log.exception(e)
    raise e


def try_except_decorator(f):
    """A decorator that wraps the passed in function in order to handle exceptions and log a message suggesting to get help or provide feedback on github."""

    def wrapper(*args, **kw):
        try:
            return f(*args, **kw)
        except Exception as e:
            exception_handler(e)

    return wrapper


def read_yaml_file(path_to_file, resolve=True):
    """Reads a yaml file.

    :param path_to_file: The path to the yaml file
    :type path_to_file: str
    :param resolve: Whether to resolve the config, defaults to True
    :type resolve: bool, optional
    :return: The config
    :rtype: Dict[str, Any]
    """
    with open(path_to_file, "r") as f:
        cfg = OmegaConf.load(f)

    cfg = OmegaConf.to_container(cfg, resolve=resolve)
    return cfg

def encode_image(image_path):
    """Encodes an image to base64."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def encode_from_buffer(buffer):
    """Encodes a buffer (typically an image from a video) to base64."""
    return base64.b64encode(buffer).decode("utf-8")


def find_replace_in_dict(cfg, key_to_find, new_value,current_path=""):
    """Recursively searches for keys == key_to_find in a dictionary and replaces its value with new_value.
    note1: it replaces each key == key_to_find, whever it is nested in the dictionary or not.
    note2: we recommend to only use this function in the Quick Start tutorial, and not in production code.
    
    :param cfg: The dictionary to search in
    :type cfg: Dict[str, Any]
    :param key_to_find: The key to find
    :type key_to_find: str
    :param new_value: The new value to set
    :type new_value: Any
    :param current_path: The current path, defaults to ""
    :type current_path: str, optional
    :return: The updated dictionary
    :rtype: Dict[str, Any]
    """
    if not isinstance(cfg, collections.abc.Mapping):
        return cfg
    for key, item in cfg.items():
        new_path = current_path + "." + key if current_path != "" else key
        if key_to_find == key:
            cfg[key] = new_value
        elif isinstance(item, collections.abc.Mapping):
            find_replace_in_dict(cfg.get(key), key_to_find, new_value, new_path)
        elif isinstance(item, list):
            cfg[key] = [find_replace_in_dict(x, key_to_find, new_value, new_path) for x in item]
    return cfg

def quick_load_api_keys(cfg, api_information: List[ApiInfo], key="api_infos"):
    """ Recursively loads the api_information in a dictionary in any field where the key is the parameter key
    
    :param cfg: The dictionary to update
    :type cfg: Dict[str, Any]
    :param api_information: The api information to set
    :type api_information: List[ApiInfo]
    :param key: The key to use, defaults to 'api_infos'
    :type key: str, optional
    """
    api_info_cfg = [
        {
            "_target_": "aiflows.backends.api_info.ApiInfo",
            "backend_used": api_info.backend_used,
            "api_key": api_info.api_key,
            "api_base": api_info.api_base
        }
    for api_info in api_information
    ]
    quick_load(cfg, api_info_cfg, key)
        
    

def quick_load(cfg, item, key="api_infos"):
    """Recursively loads the config item in a dictionary with key.
    :param cfg: The dictionary to update
    :type cfg: Dict[str, Any]
    :param item: The item to set
    :type item: Dict[str, Any]
    :param key: The key to use, defaults to 'api_infos'
    :type key: str, optional

    example:
    cfg = {
         'backend': {
            'api_infos': '???',
            'model_name': {
                'openai': 'gpt-4',
                'azure': 'azure/gpt-4'
                }
            }
         'Executor' : {
            'subflows_config': {
                    'backend': {
                    'api_infos': '???',
                    'model_name': {
                        'openai': 'gpt-4',
                        'azure': 'azure/gpt-4'
                        }
                    }
                }
            }
        }
    api_information = [ApiInfo(backend_used="openai", api_key=os.getenv("OPENAI_API_KEY"))]
    quick_load(cfg, api_information)
    returns: cfg = {
            'backend': {
                'api_infos': [ApiInfo(backend_used="openai", api_key=os.getenv("OPENAI_API_KEY"))],
                'model_name': {
                    'openai': 'gpt-4',
                    'azure': 'azure/gpt-4'
                    }
                }
            'Executor' : {
                'subflows_config': {
                        'backend': {
                        'api_infos': [ApiInfo(backend_used="openai", api_key=os.getenv("OPENAI_API_KEY"))],
                        'model_name': {
                            'openai': 'gpt-4',
                            'azure': 'azure/gpt-4'
                            }
                        }
                    }
                }
            }
    """
    if isinstance(cfg, dict):
        if key in cfg and cfg[key] == "???":
            cfg[key] = item
        for k, v in cfg.items():
            quick_load(v, item, key)
    elif isinstance(cfg, list):
        for elem in cfg:
            quick_load(elem, item, key)

