from typing import Dict, Any
import grpc
import uuid
import json
from termcolor import colored
from copy import deepcopy
import colink as CL
from colink import CoLink
import pickle
from aiflows.utils.general_helpers import (
    recursive_dictionary_update,
)
from copy import deepcopy
from aiflows.utils.io_utils import coflows_serialize, coflows_deserialize
from aiflows.base_flows import AtomicFlow
from aiflows.utils import colink_utils
import hydra
from aiflows.utils.constants import (
    COFLOWS_PATH,
    MOUNT_ARGS_TRANSFER_PATH,
    INSTANCE_METADATA_PATH,
    INSTANTIATION_METHODS,
    SERVE_MODES,
)


def is_flow_served(cl: CoLink, flow_type: str) -> bool:
    serve_entry_path = f"{COFLOWS_PATH}:{flow_type}"

    served = coflows_deserialize(cl.read_entry(f"{serve_entry_path}:init"))
    if served == 1:
        return True
    return False


def serve_flow(
    cl: CoLink,
    flow_type: str,
    serve_mode: str = "statefull",
    default_config: Dict[str, Any] = None,
    default_state: Dict[str, Any] = None,
    default_dispatch_point: str = None,
) -> bool:
    """
    Serves the flow config under the identifier flow_type.
    After serving, users can get an instance of the served flow via the get_instance operation.

    :return: True if the flow was successfully served; False if the flow is already served or an error occurred.
    :rtype: bool
    """
    serve_entry_path = f"{COFLOWS_PATH}:{flow_type}"

    if is_flow_served(cl, flow_type):
        print(
            f"{flow_type} is already being served at {serve_entry_path}"
        )
        return False

    if serve_mode not in SERVE_MODES:
        print(
            f"Invalid serve_mode '{serve_mode}'. Use one of {', '.join(SERVE_MODES)}"
        )
        return False

    # TODO validate config
    target = default_config["_target_"]
    if target.split(".")[-1] in INSTANTIATION_METHODS:
        target = ".".join(target.split(".")[:-1])

    flow_class = hydra.utils.get_class(target)
    default_config = flow_class.get_config(**deepcopy(default_config))

    if default_state is None and default_config is not None:
        default_state = default_config.get("init_state", None)

    # serve
    try:
        cl.update_entry(
            f"{serve_entry_path}:init", coflows_serialize(1)
        )
        cl.update_entry(
            f"{serve_entry_path}:serve_mode", coflows_serialize(serve_mode)
        )

        if default_config is not None:
            cl.update_entry(
                f"{serve_entry_path}:default_config",
                coflows_serialize(default_config),
            )

        # maybe remove default_state altogether
        if default_state is not None:
            cl.update_entry(
                f"{serve_entry_path}:default_state",
                coflows_serialize(default_state, use_pickle=True),
            )

        if default_dispatch_point is not None:
            cl.update_entry(
                f"{serve_entry_path}:default_dispatch_point",
                default_dispatch_point,
            )

    except grpc.RpcError:
        return False

    print(f"Started serving at {serve_entry_path}.")
    return True


def delete_served_flow(cl: CoLink, flow_type: str):
    """
    Deletes all colink entries associated with given flow_type. This includes deleting all instances of this flow_type.
    """
    serve_entry_path = f"{COFLOWS_PATH}:{flow_type}"

    try:
        # delete associated instance metadata
        mount_users_keys = cl.read_keys(
            prefix=f"{cl.get_user_id()}::{serve_entry_path}:mounts", include_history=False
        )
        for storage_entry in mount_users_keys:
            mount_keys = cl.read_keys(prefix=storage_entry.key_path.split("@")[0], include_history=False)
            for mount_key_path in mount_keys:
                instance_id = str(mount_key_path).split("::")[1].split("@")[0].split(":")[-1]
                try:
                    cl.delete_entry(f"{INSTANCE_METADATA_PATH}:{instance_id}")
                    print(f"Deleted flow instance {instance_id}")
                    # TODO delete mailbox in scheduler
                except grpc.RpcError:
                    print(f"WARNING: flow {instance_id} is mounted but it's metadata doesn't exist.")
                    continue

        colink_utils.delete_entries_on_path(cl, serve_entry_path)
        print(f"Stopped serving at {serve_entry_path}")
    except grpc.RpcError as e:
        print(f"Received RPC exception: code={e.code()} message={e.details()}")


def unserve_flow(cl: CoLink, flow_type: str):
    """
    Unserves flow - users will no longer be able to get instances of this flow_type. All live instances of this flow_type remain alive.
    """
    if not is_flow_served(cl, flow_type):
        print(f"{flow_type} wasn't being served.")
        return

    serve_entry_path = f"{COFLOWS_PATH}:{flow_type}"
    try:
        cl.update_entry(
            f"{serve_entry_path}:init", coflows_serialize(0)
        )
    except grpc.RpcError as e:
        print(f"Received RPC exception: code={e.code()} message={e.details()}")
        return

    print(f"{flow_type} has been unserved.")


def get_instance_metadata(cl: CoLink, flow_id: str):
    instance_metadata = coflows_deserialize(
        cl.read_entry(f"{INSTANCE_METADATA_PATH}:{flow_id}")
    )

    return instance_metadata


def delete_flow_instance(cl: CoLink, flow_id: str):
    """
    Deletes all colink entries associated with flow instance.
    """
    instance_metadata = get_instance_metadata(cl, flow_id)
    if instance_metadata is None:
        print(f"Metadata for {flow_id} doesn't exist.")
        return
    flow_type = instance_metadata["flow_type"]
    user_id = instance_metadata["user_id"]
    client_id = "local" if user_id == cl.get_user_id() else user_id

    serve_entry_path = f"{COFLOWS_PATH}:{flow_type}"
    mount_path = f"{serve_entry_path}:mounts:{client_id}:{flow_id}"
    metadata_path = f"{INSTANCE_METADATA_PATH}:{flow_id}"

    colink_utils.delete_entries_on_path(cl, mount_path)
    colink_utils.delete_entries_on_path(cl, metadata_path)
    print(f"Deleted flow instance {flow_id}.")

    # TODO delete mailbox in scheduler

def recursive_delete_flow_instance(cl: CoLink, flow_id: str):
    # this is "recursive unmount"
    # TODO
    ...

def recursive_serve_flow(
    cl: CoLink,
    flow_type: str,
    serving_mode="statefull",
    default_config: Dict[str, Any] = None,
    default_state: Dict[str, Any] = None,
    default_dispatch_point: str = None,
) -> bool:

    # expand default config to full default_config

    # ugly hack to get class but not sure how else to do if
    target = default_config["_target_"]

    if target.split(".")[-1] in INSTANTIATION_METHODS:
        target = ".".join(target.split(".")[:-1])

    flow_class = hydra.utils.get_class(target)
    flow_full_config = flow_class.get_config(**deepcopy(default_config))

    # if there's recursive serving, serve subflows first
    if "subflows_config" in flow_full_config:
        for subflow, subflow_config in flow_full_config["subflows_config"].items():
            # A flow is proxy if it's type is AtomicFlow or Flow (since no run method is implemented in these classes)
            # TODO: Check if this is sufficient

            needs_serving = subflow_config.get("user_id", "local") == "local"
            # if the flow is not a proxy, we must serve it and then make it become a proxy in the default_config
            if needs_serving:
                # This is ok because name is a required field in the config
                # note that if you don't specify the flow type, I'll assume it's the name of the subflow + _served
                # This means that if you don't specify the flow type, 2 subflows of the same class will be served at 2 different locations (won't share state)
                # If you want to share state, you must specify the flow type
                subflow_type = subflow_config.get("flow_type", f"{subflow}_served")
                subflow_default_state = subflow_config.get("init_state", None)
                # serve_flow returns false when an error occurs or if a flow is already served... (shouldn't we distinguish these cases?)
                # I would almost fail here if the error here
                # whereas if the flow is already serving that's great, nothing to be done
                # Which is why I called the output serving succesful

                subflow_target = subflow_config["_target_"]

                if subflow_target.split(".")[-1] in INSTANTIATION_METHODS:
                    subflow_target = ".".join(subflow_target.split(".")[:-1])

                subflow_class = hydra.utils.get_class(subflow_target)

                # Mauro suggestion: serve the default configuration all the time for subflows (mount overrieds stuff)
                subflow_cfg = subflow_class.get_config()
                subflow_cfg["_target_"] = subflow_config["_target_"]
                serving_succesful = recursive_serve_flow(
                    cl=cl,
                    flow_type=subflow_type,
                    # TODO: shouldn't this be read from yaml file of subflow (find it in flow_modules directory)
                    default_config=subflow_cfg,
                    default_state=subflow_default_state,
                    default_dispatch_point=default_dispatch_point,
                )

                # Change the subflow_config of flow to proxy
                # Quite ugly, but what am I supposed to do?

                if subflow not in default_config["subflows_config"]:
                    default_config["subflows_config"][subflow] = {}

                default_config["subflows_config"][subflow][
                    "_target_"
                ] = f"aiflows.base_flows.AtomicFlow.instantiate_from_default_config"
                default_config["subflows_config"][subflow]["user_id"] = "local"
                default_config["subflows_config"][subflow]["flow_type"] = subflow_type
                if "name" not in default_config["subflows_config"][subflow]:
                    default_config["subflows_config"][subflow]["name"] = subflow_cfg[
                        "name"
                    ]
                if "description" not in subflow_config:
                    default_config["subflows_config"][subflow][
                        "description"
                    ] = subflow_cfg["description"]

    serving_succesful = serve_flow(
        cl=cl,
        flow_type=flow_type,
        serving_mode=serving_mode,
        default_config=default_config,
        default_state=default_state,
        default_dispatch_point=default_dispatch_point,
    )
    return serving_succesful


def mount(
    cl: CoLink,
    client_id: str,
    flow_type: str,
    config_overrides: Dict[str, Any] = None,
    initial_state: Dict[str, Any] = None,
    dispatch_point_override: str = None,
) -> AtomicFlow:
    """
    Mounts a new instance of the specified flow type by creating necessary entries in CoLink storage.

    :return: unique flow reference string
    :rtype: aiflows.base_flows.AtomicFlow
    """
    serve_entry_path = f"{COFLOWS_PATH}:{flow_type}"
    if not is_flow_served(cl, flow_type):
        print(
            f"Can't create instance - {flow_type} is not being served."
        )
        return None

    # if served flow is singleton, return existing flow_ref

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

        serve_entry_path = f"{COFLOWS_PATH}:{flow_type}"

        # If user set an initial state, keep it.
        # Otherwise take the default one initialized when started serving
        initial_state = (
            initial_state
            if initial_state is not None
            else coflows_deserialize(
                cl.read_entry(f"{serve_entry_path}:default_state"), use_pickle=True
            )
        )

        if initial_state is not None:
            cl.create_entry(
                f"{mount_path}:state",
                coflows_serialize(initial_state, use_pickle=True),
            )

        if dispatch_point_override is not None:
            cl.create_entry(
                f"{mount_path}:dispatch_point_override",
                dispatch_point_override,
            )

    except grpc.RpcError as e:
        raise e

    print(f"Mounted {flow_ref} at {mount_path}")

    ##TODO: Maybe we want to add all the info to the proxy, let's see
    name = f"Proxy_{flow_type}"
    description = f"Proxy of {flow_type}"

    proxy_overrides = {
        "name": name,
        "description": description,
        "user_id": client_id,
        "flow_ref": str(flow_ref),
        "flow_type": flow_type,
    }

    proxy_flow = AtomicFlow.instantiate_from_default_config(**proxy_overrides)

    proxy_flow.set_colink(cl)

    return proxy_flow


def recursive_mount(
    cl: CoLink,
    client_id: str,
    flow_type: str,
    config_overrides: Dict[str, Any] = None,
    initial_state: Dict[str, Any] = None,
    dispatch_point_override: str = None,
) -> AtomicFlow:
    serve_entry_path = f"{COFLOWS_PATH}:{flow_type}"
    if not is_flow_served(cl, flow_type):
        print(
            f"Can't create instance - {flow_type} is not being served."
        )
        return None

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

            # TODO: Check if you this deprication is approved
            # subflow_config_overrides = None
            # if "config_overrides" in subflow_config:
            #     subflow_config_overrides = subflow_config["config_overrides"]

            # And replace with this
            subflow_config_overrides = deepcopy(subflow_config)
            subflow_config_overrides.pop("_target_", None)

            if user_id == "local":
                proxy = recursive_mount(
                    cl, user_id, subflow_type, subflow_config_overrides
                )
                if proxy is None:
                    print("WARNING: can't create subflow. Some instances might have been created, while others didn't.")
                    # TODO delete all other created instances
                    return None

                if config_overrides is None:
                    config_overrides = {}
                if "subflows_config" not in config_overrides:
                    config_overrides["subflows_config"] = {}
                if subflow_key not in config_overrides["subflows_config"]:
                    config_overrides["subflows_config"][subflow_key] = {}

                config_overrides["subflows_config"][subflow_key][
                    "flow_ref"
                ] = proxy.flow_config["flow_ref"]
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

    proxy_flow = mount(
        cl,
        client_id,
        flow_type,
        config_overrides,
        initial_state,
        dispatch_point_override,
    )

    return proxy_flow


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
