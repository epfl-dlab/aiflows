from colink import CoLink, InstantServer, InstantRegistry
from aiflows.utils.io_utils import coflows_deserialize
from aiflows.utils.constants import (
    COFLOWS_PATH,
    INSTANCE_METADATA_PATH,
)


def start_colink_server() -> CoLink:
    InstantRegistry()
    cl = InstantServer().get_colink().switch_to_generated_user()
    cl.start_protocol_operator("coflows_scheduler", cl.get_user_id(), False)
    return cl


def recursive_print_keys(cl: CoLink, path, print_values=False, indent=0):
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
    recursive_print_keys(cl, COFLOWS_PATH, print_values)


def print_flow_instances(cl: CoLink, print_values=False):
    recursive_print_keys(cl, INSTANCE_METADATA_PATH, print_values)


def delete_entries_on_path(cl: CoLink, path):
    keys = cl.read_keys(prefix=f"{cl.get_user_id()}::{path}", include_history=False)

    for key_path in keys:
        key_name = str(key_path).split("::")[1].split("@")[0]
        delete_entries_on_path(cl, key_name)

    if cl.read_entry(path) is not None:
        cl.delete_entry(path)
