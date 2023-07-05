import collections
from pathlib import Path
from typing import List
import uuid
import time
import os

import json
import jsonlines
import gzip

from omegaconf import OmegaConf

from flows import logging
log = logging.get_logger(__name__)


def validate_parameters(cls, kwargs):
    if cls.__name__ != "Flow":
        cls.__base__._validate_parameters(kwargs)

    flow_config = kwargs["flow_config"]

    if not hasattr(cls, "REQUIRED_KEYS_CONFIG"):
        raise ValueError("REQUIRED_KEYS_CONFIG should be defined for each Flow class.")

    for key in cls.REQUIRED_KEYS_CONFIG:
        if key not in flow_config:
            raise ValueError(f"{key} is a required parameter in the flow_config.")

    if not hasattr(cls, "REQUIRED_KEYS_CONSTRUCTOR"):
        raise ValueError("REQUIRED_KEYS_CONSTRUCTOR should be defined for each Flow class.")

    for key in cls.REQUIRED_KEYS_CONSTRUCTOR:
        if key not in kwargs:
            raise ValueError(f"{key} is a required parameter in the constructor.")


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
        if isinstance(v, collections.abc.Mapping):
            d[k] = recursive_dictionary_update(d.get(k, {}), v)
        else:
            d[k] = v
    return d


def read_yaml_file(path_to_file, resolve=True):
    with open(path_to_file, "r") as f:
        cfg = OmegaConf.load(f)

    cfg = OmegaConf.to_container(cfg, resolve=resolve)
    return cfg

