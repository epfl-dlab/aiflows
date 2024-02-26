from typing import Dict, Any
import grpc
import uuid
import json
from termcolor import colored

import colink as CL
from colink import CoLink

from aiflows.utils.general_helpers import (
    recursive_dictionary_update,
)
from aiflows.utils.coflows_utils import coflows_serialize, coflows_deserialize


COFLOWS_PATH = "flows"
MOUNT_ARGS_TRANSFER_PATH = "mount_tasks"
INSTANCE_METADATA_PATH = "instance_metadata"  # should remove after extending engine


def serve_flow(
    cl: CoLink,
    flow_type: str,
    default_config: Dict[str, Any] = None,
    default_state: Dict[str, Any] = None,
    default_dispatch_point: str = None,
) -> bool:
    """
    Serves the specified flow type by creating necessary entries in CoLink storage.
    After serving, users can create new instances of the served flow type via the mount operation.

    :return: True if the flow was successfully served; False if the flow is already served or an error occurred.
    :rtype: bool
    """
    serve_entry_path = f"{COFLOWS_PATH}:{flow_type}"
    serve_entry = cl.read_entry(f"{serve_entry_path}:init")
    if serve_entry is not None:
        print(
            f"{flow_type} is already being served. Found serve entry at path {serve_entry_path}"
        )
        return False

    try:
        cl.create_entry(
            f"{serve_entry_path}:init", coflows_serialize(f"init {flow_type}")
        )

        if default_config is not None:
            cl.create_entry(
                f"{serve_entry_path}:default_config",
                coflows_serialize(default_config),
            )

        # probably remove this default_state
        if default_state is not None:
            cl.create_entry(
                f"{serve_entry_path}:default_state",
                coflows_serialize(default_state),
            )

        if default_dispatch_point is not None:
            cl.create_entry(
                f"{serve_entry_path}:default_dispatch_point",
                default_dispatch_point,
            )

    except grpc.RpcError:
        return False

    print(f"Started serving at {serve_entry_path}.")
    return True


def recursive_serve_flow(
    cl: CoLink,
    flow_type: str,
    default_config: Dict[str, Any] = None,
    default_state: Dict[str, Any] = None,
    default_dispatch_point: str = None,
) -> bool:
    # how to handle subflow configs ? need to read them from flow_modules
    ...


def mount(
    cl: CoLink,
    client_id: str,
    flow_type: str,
    config_overrides: Dict[str, Any] = None,
    initial_state: Dict[str, Any] = None,
    dispatch_point_override: str = None,
) -> uuid.UUID:
    """
    Mounts a new instance of the specified flow type by creating necessary entries in CoLink storage.

    :return: unique flow reference string
    :rtype: uuid.UUID
    """
    serve_entry_path = f"{COFLOWS_PATH}:{flow_type}"
    if cl.read_entry(f"{serve_entry_path}:init") is None:
        print(
            f"{flow_type} is not being served. No entry found at path {serve_entry_path}:init"
        )
        return False

    flow_ref = uuid.uuid4()
    mount_path = f"{serve_entry_path}:mounts:{client_id}:{flow_ref}"

    if config_overrides is None:
        config_overrides = {}
    config_overrides["flow_ref"] = str(flow_ref)

    try:
        cl.create_entry(
            f"{mount_path}:init",
            coflows_serialize(f"init client:{client_id}, flow_type:{flow_type}"),
        )
        instance_metadata = {"flow_type": flow_type, "user_id": client_id}
        cl.create_entry(
            f"{INSTANCE_METADATA_PATH}:{flow_ref}", coflows_serialize(instance_metadata)
        )  # This should be added to queues data structure along with (maybe overriden) dispatch_point

        cl.create_entry(
            f"{mount_path}:config_overrides",
            coflows_serialize(config_overrides),
        )

        if initial_state is not None:
            cl.create_entry(
                f"{mount_path}:state",
                coflows_serialize(initial_state),
            )

        if dispatch_point_override is not None:
            cl.create_entry(
                f"{mount_path}:dispatch_point_override",
                dispatch_point_override,
            )

    except grpc.RpcError as e:
        raise e

    print(f"Mounted {flow_ref} at {mount_path}")
    return str(flow_ref)


def recursive_mount(
    cl: CoLink,
    client_id: str,
    flow_type: str,
    config_overrides: Dict[str, Any] = None,
    initial_state: Dict[str, Any] = None,
    dispatch_point_override: str = None,
) -> uuid.UUID:
    serve_entry_path = f"{COFLOWS_PATH}:{flow_type}"
    if cl.read_entry(f"{serve_entry_path}:init") is None:
        print(
            f"{flow_type} is not being served. No entry found at path {serve_entry_path}:init"
        )
        return False

    config = coflows_deserialize(cl.read_entry(f"{serve_entry_path}:default_config"))

    if config_overrides is not None:
        config = recursive_dictionary_update(config, config_overrides)

    participants = [CL.Participant(user_id=cl.get_user_id(), role="initiator")]
    mount_initiator_args = {}
    # user_id -> [(subflow_key, subflow_type, subflow_config_overrides)]

    if "subflows_config" in config:
        for subflow_key, subflow_config in config["subflows_config"].items():
            if "flow_ref" in subflow_config:
                # subflow already mounted
                continue

            if "user_id" not in subflow_config or "flow_type" not in subflow_config:
                continue

            user_id = subflow_config["user_id"]
            subflow_type = subflow_config["flow_type"]

            subflow_config_overrides = None
            if "config_overrides" in subflow_config:
                subflow_config_overrides = subflow_config["config_overrides"]

            if user_id == "local":
                flow_ref = recursive_mount(
                    cl, user_id, subflow_type, subflow_config_overrides
                )

                if config_overrides is None:
                    config_overrides = {}
                if "subflows_config" not in config_overrides:
                    config_overrides["subflows_config"] = {}
                if subflow_key not in config_overrides["subflows_config"]:
                    config_overrides["subflows_config"][subflow_key] = {}

                config_overrides["subflows_config"][subflow_key]["flow_ref"] = flow_ref
            else:
                if user_id not in mount_initiator_args:
                    mount_initiator_args[user_id] = []
                    participants.append(
                        CL.Participant(user_id=user_id, role="receiver")
                    )

                mount_initiator_args[user_id].append(
                    (subflow_key, subflow_type, subflow_config_overrides)
                )

        if len(participants) > 1:
            mount_id = uuid.uuid4()
            cl.create_entry(
                f"{MOUNT_ARGS_TRANSFER_PATH}:{mount_id}:mount_args",
                coflows_serialize(mount_initiator_args),
            )
            task_id = cl.run_task(
                "coflows_mount", coflows_serialize(mount_id), participants, True
            )

            cl.wait_task(task_id)

            flow_refs = coflows_deserialize(
                cl.read_entry(f"{MOUNT_ARGS_TRANSFER_PATH}:{mount_id}:flow_refs")
            )  # subflow_keys should be unique
            for subflow_key, flow_ref in flow_refs.items():
                if "subflows_config" not in config_overrides:
                    config_overrides["subflows_config"] = {}
                if subflow_key not in config_overrides["subflows_config"]:
                    config_overrides["subflows_config"][subflow_key] = {}

                config_overrides["subflows_config"][subflow_key]["flow_ref"] = flow_ref

    flow_ref = mount(
        cl,
        client_id,
        flow_type,
        config_overrides,
        initial_state,
        dispatch_point_override,
    )
    return flow_ref


def start_colink_component(component_name: str, args):
    print(
        colored(
            r"""
         _    ________
  ____ _(_)  / ____/ /___ _      _______
 / __ `/ /  / /_  / / __ \ | /| / / ___/
/ /_/ / /  / __/ / / /_/ / |/ |/ (__  )
\__,_/_/  /_/   /_/\____/|__/|__/____/""",
            "blue",
        )
    )
    print(colored(f"{component_name}\n", "grey", attrs=["bold"]))

    print(colored(json.dumps(args, indent=4), "white"))
    print("\n")

    print("Connecting to colink server...")
    cl = CoLink(args["addr"], args["jwt"])
    print(f"Connected to {cl.get_core_addr()} as user {cl.get_user_id()}\n")
    return cl
