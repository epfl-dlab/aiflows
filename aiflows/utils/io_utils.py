import os
import pickle
import json
from typing import Any


def load_pickle(pickle_path: str):
    """Loads data from a pickle file.

    :param pickle_path: The path to the pickle file
    :type pickle_path: str
    :return: The data loaded from the pickle file
    :rtype: Any
    """
    # Check if the provided path is valid
    if not os.path.isfile(pickle_path):
        raise FileNotFoundError(f"Checkpoint file not found at {pickle_path}")

    # Load data from the checkpoint file using pickle
    with open(pickle_path, "rb") as file:
        data = pickle.load(file)

    return data


def recursive_json_serialize(obj):
    """Recursively serializes an object to json.

    :param obj: The object to serialize
    :type obj: Any
    :return: The serialized object
    :rtype: Any
    """
    if isinstance(obj, (list, tuple)):
        return [recursive_json_serialize(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: recursive_json_serialize(value) for key, value in obj.items()}
    elif hasattr(obj, "to_json"):
        return recursive_json_serialize(obj.to_json())
    else:
        return obj


def coflows_serialize(data: Any, use_pickle=False) -> bytes:
    """ Serializes the given data.
    
    :param data: data to serialize
    :type data: Any
    :param use_pickle: whether to use pickle for serialization (default is False)
    :type use_pickle: bool
    """
    if use_pickle:
        return pickle.dumps(data)

    json_str = json.dumps(data)
    return json_str.encode("utf-8")


def coflows_deserialize(encoded_data: bytes, use_pickle=False) -> Any:
    """ Deserializes the given data.
    
    :param encoded_data: data to deserialize
    :type encoded_data: bytes
    :param use_pickle: whether to use pickle for deserialization (default is False)
    :type use_pickle: bool
    """
    if encoded_data is None:
        return None
    if use_pickle:
        return pickle.loads(encoded_data)
    try:
        json_str = encoded_data.decode("utf-8")
        return json.loads(json_str)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return encoded_data
