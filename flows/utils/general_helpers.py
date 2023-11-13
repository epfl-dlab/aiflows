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
from litellm.utils import function_to_dict
from flows import logging
import base64

log = logging.get_logger(__name__)


def validate_flow_config(cls, flow_config):
    if cls.__name__ != "Flow":
        cls.__base__._validate_flow_config(flow_config)

    if not hasattr(cls, "REQUIRED_KEYS_CONFIG"):
        raise ValueError("REQUIRED_KEYS_CONFIG should be defined for each Flow class.")

    for key in cls.REQUIRED_KEYS_CONFIG:
        if key not in flow_config:
            raise ValueError(f"{key} is a required parameter in the flow_config.")


def flatten_dict(d, parent_key='', sep='.'):
    items = []
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


# Function to unflatten dictionary
def unflatten_dict(d, sep='.'):
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

    Args:
        data_dict (dict): The dictionary to pop from.
        nested_key (str): The nested key to pop, in the format "key1.key2.key3".

    Returns:
        None
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

    Args:
        data_dict (dict): The dictionary to update.
        nested_key (str): The nested key to update, in the format "key1.key2.key3".
        value (Any): The new value to set for the nested key.

    Returns:
        None
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
    
    Args:
    - search_dict: dict - The dictionary to search in.
    - nested_key: str - The composite key string to search for.
    
    Returns:
    - tuple - A tuple containing the value of the nested key and a boolean indicating if the key was found.
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
    with open(path_to_file, "r") as f:
        json_reader = jsonlines.Reader(f)
        return list(json_reader)


def write_jsonlines(path_to_file, data, mode="w"):
    with jsonlines.open(path_to_file, mode) as writer:
        writer.write_all(data)


def write_gzipped_jsonlines(path_to_file, data, mode="w"):
    with gzip.open(path_to_file, mode) as fp:
        json_writer = jsonlines.Writer(fp)
        json_writer.write_all(data)


def read_gzipped_jsonlines(path_to_file):
    with gzip.open(path_to_file, "r") as fp:
        json_reader = jsonlines.Reader(fp)
        return list(json_reader)


def create_unique_id(existing_ids: List[str] = None):
    if existing_ids is None:
        existing_ids = set()

    while True:
        unique_id = str(uuid.uuid4())
        if unique_id not in existing_ids:
            return unique_id


def get_current_datetime_ns():
    time_of_creation_ns = time.time_ns()

    # Convert nanoseconds to seconds and store as a time.struct_time object
    time_of_creation_struct = time.gmtime(time_of_creation_ns // 1000000000)

    # Format the time.struct_time object into a human-readable string
    formatted_time_of_creation = time.strftime("%Y-%m-%d %H:%M:%S", time_of_creation_struct)

    # Append the nanoseconds to the human-readable string
    formatted_time_of_creation += f".{time_of_creation_ns % 1000000000:09d}"

    return formatted_time_of_creation


def get_predictions_dir_path(output_dir, create_if_not_exists=True):
    if output_dir is not None:
        predictions_folder = os.path.join(output_dir, "predictions")
    else:
        predictions_folder = "predictions"

    if create_if_not_exists:
        Path(predictions_folder).mkdir(parents=True, exist_ok=True)

    return predictions_folder


def write_outputs(path_to_output_file, summary, mode):
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
    """Performs a recursive update of the values in dictionary d with the values of dictionary u"""
    if d is None:
        d = {}
    for k, v in u.items():
        if isinstance(v, collections.abc.Mapping) and isinstance(d.get(k, {}),  collections.abc.Mapping):
            d[k] = recursive_dictionary_update(d.get(k, {}), v)
        else:
            d[k] = v
    return d


def read_yaml_file(path_to_file, resolve=True):
    with open(path_to_file, "r") as f:
        cfg = OmegaConf.load(f)

    cfg = OmegaConf.to_container(cfg, resolve=resolve)
    return cfg


def python_file_path_to_module_path(file_path):
    return file_path.replace("/",".").replace(".py","")

def python_module_path_to_file_path(module_path):
    return module_path.replace(".","/") + ".py"

def extract_top_level_function_names(python_file_path):
    """Extracts the top level function names from a python file (ignores nested)"""
    function_names = []
    with open(python_file_path, 'r') as file:
        file_content = file.read()
        tree = ast.parse(file_content)
    
    functions = filter(lambda node: isinstance(node, ast.FunctionDef),ast.iter_child_nodes(tree))
    function_names = list(map(lambda node: node.name,functions))

    return function_names

def get_function_meta_data(function):
    return function_to_dict(function)

def get_function_from_name(function_name,module):
    return getattr(module,function_name)

def get_pyfile_functions_metadata_from_file(python_file_path):
    function_names = extract_top_level_function_names(python_file_path)
    module_path = python_file_path_to_module_path(python_file_path)
    module = importlib.import_module(module_path)
    functions = [get_function_from_name(function_name,module) for function_name in function_names]
    return [get_function_meta_data(function) for function in functions]

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')
    
def encode_from_buffer(buffer):
    return base64.b64encode(buffer).decode("utf-8")