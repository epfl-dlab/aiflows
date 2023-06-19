import collections
from pathlib import Path
from typing import List
import uuid
import time
import os

import json
import jsonlines
import gzip


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
        return json.dumps(obj, default=to_dict_serializer)

    with open(path_to_output_file, mode) as fp:
        json_writer = jsonlines.Writer(fp, dumps=to_dict_dumps)
        json_writer.write_all(summary)


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
