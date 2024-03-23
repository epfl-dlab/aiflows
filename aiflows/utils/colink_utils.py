from typing import List
from colink import CoLink, InstantServer, InstantRegistry
from aiflows.utils.io_utils import coflows_deserialize
from aiflows.utils.constants import (
    COFLOWS_PATH,
    INSTANCE_METADATA_PATH,
)


def start_colink_server() -> CoLink:
    """ Starts a colink server and returns a colink object with a generated user."""
    InstantRegistry()
    cl = InstantServer().get_colink().switch_to_generated_user()
    cl.start_protocol_operator("coflows_scheduler", cl.get_user_id(), False)
    return cl


def start_colink_server_with_users(num_users: int = 1) -> List[CoLink]:
    """ Starts a colink server and returns a list of colink objects with generated users.
    
    :param num_users: number of users to create
    :type num_users: int
    :return: list of colink objects (one for each user)
    """
    InstantRegistry()
    is0 = InstantServer()
    colinks = []
    for i in range(num_users):
        cl = is0.get_colink().switch_to_generated_user()
        cl.start_protocol_operator("coflows_scheduler", cl.get_user_id(), False)
        colinks.append(cl)
    return colinks


def recursive_print_keys(cl: CoLink, path, print_values=False, indent=0):
    """ Recursively prints the keys in the given path.
    
    :param cl: colink object
    :type cl: CoLink
    :param path: path to print
    :type path: str
    :param print_values: whether to print the values of the keys (default is False)
    :type print_values: bool
    :param indent: indentation level
    :type indent: int
    """
    # TODO stop printing folders that were deleted
    keys = cl.read_keys(prefix=f"{cl.get_user_id()}::{path}", include_history=False)

    for key_path in keys:
        key_name = str(key_path).split("::")[1].split("@")[0]
        entry = coflows_deserialize(cl.read_entry(key_name))

        print(" " * indent, key_name.split(":")[-1], end="")
        if entry is None:
            print("/")
        elif print_values:
            print(":", entry)
        else:
            print("")
        recursive_print_keys(cl, key_name, print_values, indent + 2)


def print_served_flows(cl: CoLink, print_values=False):
    """ Prints the served flows of the given colink object.
    
    :param cl: colink object
    :type cl: CoLink
    :param print_values: whether to print the values of the keys (default is False)
    :type print_values: bool
    """
    recursive_print_keys(cl, COFLOWS_PATH, print_values)


def print_flow_instances(cl: CoLink, print_values=False):
    """ Prints the flow instances of the given colink object.
    
    :param cl: colink object
    :type cl: CoLink
    :param print_values: whether to print the values of the keys (default is False)
    :type print_values: bool
    """
    recursive_print_keys(cl, INSTANCE_METADATA_PATH, print_values)


def delete_entries_on_path(cl: CoLink, path):
    """ Deletes all entries on the given path.
    
    :param cl: colink object
    :type cl: CoLink
    :param path: path to delete
    :type path: str
    """
    keys = cl.read_keys(prefix=f"{cl.get_user_id()}::{path}", include_history=False)

    for key_path in keys:
        key_name = str(key_path).split("::")[1].split("@")[0]
        delete_entries_on_path(cl, key_name)

    if cl.read_entry(path) is not None:
        cl.delete_entry(path)
