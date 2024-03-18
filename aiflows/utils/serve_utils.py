from typing import Dict, Any, List
import grpc
import uuid
import json
from termcolor import colored
from copy import deepcopy
import colink as CL
from colink import CoLink
import pickle
import os
from aiflows.utils.general_helpers import (
    recursive_dictionary_update,
    quick_load_api_keys,
)
from aiflows.backends.api_info import ApiInfo
from copy import deepcopy
from aiflows.utils.io_utils import coflows_serialize, coflows_deserialize
from aiflows.base_flows import AtomicFlow
from aiflows.utils import colink_utils
import hydra
from aiflows.utils.constants import (
    COFLOWS_PATH,
    GET_INSTANCE_CALLS_TRANSFER_PATH,
    INSTANCE_METADATA_PATH,
    INSTANTIATION_METHODS,
    DEFAULT_DISPATCH_POINT,
)


class FlowInstanceException(Exception):
    def __init__(self, flow_endpoint, user_id, message=""):
        self.flow_endpoint = (flow_endpoint,)
        self.user_id = user_id
        self.message = f"Failed to get flow instance at {flow_endpoint} served by user {user_id}.\nMessage: {message}"
        super().__init__(self.message)


def is_flow_served(cl: CoLink, flow_endpoint: str) -> bool:
    serve_entry_path = f"{COFLOWS_PATH}:{flow_endpoint}"
    served = coflows_deserialize(cl.read_entry(f"{serve_entry_path}:init"))
    if served == 1:
        return True
    return False


def serve_flow(
    cl: CoLink,
    flow_class_name: str,
    flow_endpoint: str,
    dispatch_point: str = DEFAULT_DISPATCH_POINT,
    parallel_dispatch: bool = False,
    singleton: bool = False,
    # flow_registry: str = "coflows_registry",
) -> bool:
    """
    Serves the flow specified by flow_class_name at endpoint specified by flow_endpoint.
    After serving, users can get an instance of the served flow via the get_flow_instance operation.

    :return: True if the flow was successfully served; False if the flow is already served or an error occurred.
    :rtype: bool
    """
    serve_entry_path = f"{COFLOWS_PATH}:{flow_endpoint}"
    if is_flow_served(cl, flow_endpoint):
        print(f"Already serving at {serve_entry_path}")
        return False

    # serve
    try:
        cl.update_entry(f"{serve_entry_path}:init", coflows_serialize(1))
        cl.update_entry(
            f"{serve_entry_path}:flow_class_name",
            coflows_serialize(flow_class_name),
        )
        cl.update_entry(
            f"{serve_entry_path}:default_dispatch_point",
            dispatch_point,
            # NOTE if we do coflows_serialize here, scheduler reads it with double quotation marks - breaks it.
        )
        cl.update_entry(
            f"{serve_entry_path}:singleton",
            coflows_serialize(singleton),
        )
        cl.update_entry(
            f"{serve_entry_path}:parallel_dispatch",
            parallel_dispatch,
            # NOTE scheduler reads this as a bit
        )

    except grpc.RpcError as e:
        print(f"Received RPC exception: code={e.code()} message={e.details()}")
        return False

    print(f"Started serving {flow_class_name} at {serve_entry_path}.")
    print(f"dispatch_point: {dispatch_point}")
    print(f"parallel_dispatch: {parallel_dispatch}")
    print(f"singleton: {singleton}")
    return True


def delete_flow_endpoint(cl: CoLink, flow_endpoint: str):
    """
    Deletes all colink entries at given flow_endpoint. This includes deleting all instances of this flow.
    """
    serve_entry_path = f"{COFLOWS_PATH}:{flow_endpoint}"

    try:
        # delete associated instance metadata
        mount_users_keys = cl.read_keys(
            prefix=f"{cl.get_user_id()}::{serve_entry_path}:mounts",
            include_history=False,
        )
        for storage_entry in mount_users_keys:
            mount_keys = cl.read_keys(
                prefix=storage_entry.key_path.split("@")[0], include_history=False
            )
            for mount_key_path in mount_keys:
                instance_id = (
                    str(mount_key_path).split("::")[1].split("@")[0].split(":")[-1]
                )
                try:
                    cl.delete_entry(f"{INSTANCE_METADATA_PATH}:{instance_id}")
                    print(f"Deleted flow instance {instance_id}")
                    # TODO delete mailbox in scheduler
                except grpc.RpcError:
                    print(
                        f"WARNING: flow {instance_id} is mounted but it's metadata doesn't exist."
                    )
                    continue

        colink_utils.delete_entries_on_path(cl, serve_entry_path)
        print(f"Stopped serving at {serve_entry_path}")
    except grpc.RpcError as e:
        print(f"Received RPC exception: code={e.code()} message={e.details()}")


def unserve_flow(cl: CoLink, flow_endpoint: str):
    """
    unserves flow - users will no longer be able to get instances from this flow_endpoint. all live instances created on this flow_endpoint remain alive.
    """
    if not is_flow_served(cl, flow_endpoint):
        print(f"{flow_endpoint} wasn't being served.")
        return

    serve_entry_path = f"{COFLOWS_PATH}:{flow_endpoint}"
    try:
        cl.update_entry(f"{serve_entry_path}:init", coflows_serialize(0))
    except grpc.RpcError as e:
        print(f"Received RPC exception: code={e.code()} message={e.details()}")
        return

    print(f"Stopped serving at {serve_entry_path}")


def _get_local_flow_instance_metadata(cl: CoLink, flow_id: str):
    """
    Returns dict with metadata about specified local flow instance. This includes flow_endpoint and client_id.
    """
    instance_metadata = coflows_deserialize(
        cl.read_entry(f"{INSTANCE_METADATA_PATH}:{flow_id}")
    )
    return instance_metadata


def delete_flow_instance(cl: CoLink, flow_id: str):
    """
    Deletes all colink entries associated with flow instance.
    """
    instance_metadata = _get_local_flow_instance_metadata(cl, flow_id)
    if instance_metadata is None:
        print(f"Metadata for {flow_id} doesn't exist.")
        return
    flow_endpoint = instance_metadata["flow_endpoint"]
    client_id = instance_metadata["user_id"]
    client_id = "local" if client_id == cl.get_user_id() else client_id

    serve_entry_path = f"{COFLOWS_PATH}:{flow_endpoint}"
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


def mount(
    cl: CoLink,
    client_id: str,
    flow_endpoint: str,
    config_overrides: Dict[str, Any] = None,
    initial_state: Dict[str, Any] = None,
    dispatch_point_override: str = None,
) -> AtomicFlow:
    """
    Mounts a new instance at the specified flow endpoint by creating necessary entries in CoLink storage.

    :return: proxy flow object
    :rtype: aiflows.base_flows.AtomicFlow
    """
    if not is_flow_served(cl, flow_endpoint):
        raise FlowInstanceException(
            flow_endpoint,
            cl.get_user_id(),
            f"Not serving at {flow_endpoint}.",
        )

    serve_entry_path = f"{COFLOWS_PATH}:{flow_endpoint}"
    flow_id = uuid.uuid4()
    mount_path = f"{serve_entry_path}:mounts:{client_id}:{flow_id}"

    # inject self flow_id in config
    if config_overrides is None:
        config_overrides = {}
    config_overrides["flow_id"] = str(flow_id)

    try:
        cl.create_entry(f"{mount_path}:init", coflows_serialize(1))
        # TODO should actual dispatch_point also be inside metadata
        # NOTE scheduler uses this metadata
        instance_metadata = {"flow_endpoint": flow_endpoint, "user_id": client_id}
        cl.create_entry(
            f"{INSTANCE_METADATA_PATH}:{flow_id}", coflows_serialize(instance_metadata)
        )  # This can be added to engine queues data structure along with dispatch_point

        cl.create_entry(
            f"{mount_path}:config_overrides",
            coflows_serialize(config_overrides),
        )

        # TODO we no longer have default state
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
        raise FlowInstanceException(
            flow_endpoint=flow_endpoint,
            user_id=cl.get_user_id(),
            message=f"Received RPC exception: code={e.code()} message={e.details()}",
        )

    print(f"Mounted {flow_id} at {mount_path}")

    return flow_id


def _get_remote_flow_instances(
    cl: CoLink,
    get_instance_calls,  # user_id --> List((flow_key, flow_endpoint, cfg_overrides))
) -> Dict[str, Any]:
    assert len(get_instance_calls) > 0

    participants = [CL.Participant(user_id=cl.get_user_id(), role="initiator")]
    for k, v in get_instance_calls.items():
        if len(k) < 5:
            # HACK need to validate that user_id is not e.g. ??? (5 for 'local')
            raise FlowInstanceException(
                flow_endpoint=v[0][1],
                user_id=k,
                message=f"Invalid participant id {k}",
            )
        participants.append(CL.Participant(user_id=k, role="receiver"))

    request_id = str(uuid.uuid4())
    cl.create_entry(
        f"{GET_INSTANCE_CALLS_TRANSFER_PATH}:{request_id}:get_instance_calls",
        coflows_serialize(get_instance_calls),
    )

    task_id = cl.run_task(
        "coflows_get_instances", coflows_serialize(request_id), participants, True
    )  # may throw grpc exception if user is unknown or unresponsive
    # TODO should we wrap it into FlowInstanceException ?

    cl.wait_task(task_id)

    get_instances_results = coflows_deserialize(
        cl.read_entry(
            f"{GET_INSTANCE_CALLS_TRANSFER_PATH}:{request_id}:get_instances_results"
        )
    )  # subflow_keys should be unique
    # check aiflows.workers.mount_worker.mount_receiver_handler

    return get_instances_results


def _get_collaborative_subflow_instances(
    cl: CoLink,
    client_id: str,
    subflows_config: Dict[str, Any],  # subflow_key --> subflow config
) -> Dict[str, str]:
    """
    Gets instances of specified flows. User specifies flows by passing
    subflows_config dictionary (typically extracted from the parent flow's config).
    The subflows_config dictionary should map user defined 'flow keys'
    (aliases that parent flow will use to call subflows) to flow configs.

    Every subflow instance will receive the flow ids of all other subflow instances,
    as well as the flow id of the parent flow. This will be given through
    corresponding config_overrides dicts.

    Returns a dictionary mapping flow keys to flow ids.

    :param cl: colink object
    :type cl: CoLink
    :param client_id: id of colink user making the request
    :type client_id: str
    :param subflows_config: dictionary mapping flow keys to flow configs
    :type subflows_config: Dict[str, Any]
    :return: dictionary mapping subflow keys to flow ids
    :rtype: Dict[str, str]
    """
    get_instances_results = {}  # subflow_key --> Dict
    get_instance_calls = {}
    # user_id -> [(subflow_key, subflow_endpoint, subflow_config_overrides)]

    for subflow_key, subflow_config in subflows_config.items():
        if "flow_id" in subflow_config:
            continue

        if "user_id" not in subflow_config or "flow_endpoint" not in subflow_config:
            continue

        user_id = subflow_config["user_id"]
        user_id = "local" if user_id == cl.get_user_id() else user_id
        subflow_endpoint = subflow_config["flow_endpoint"]

        subflow_config_overrides = deepcopy(subflow_config)
        # TODO maybe these should be in a single subdict
        subflow_config_overrides.pop("_target_", None)
        subflow_config_overrides.pop("user_id", None)
        subflow_config_overrides.pop("flow_endpoint", None)

        if user_id == "local":
            try:
                flow_id = _get_local_flow_instance(
                    cl=cl,
                    client_id=client_id,
                    flow_endpoint=subflow_endpoint,
                    config_overrides=subflow_config_overrides,
                    initial_state=None,  # TODO should we allow caller to override this
                    dispatch_point_override=None,
                )
                get_instances_results[subflow_key] = {
                    "flow_id": flow_id,
                    "successful": True,
                    "message": "Fetched local flow instance.",
                }
            except FlowInstanceException as e:
                get_instances_results[subflow_key] = {
                    "flow_id": "",
                    "successful": False,
                    "message": e.message,
                }
                # NOTE also check aiflows.workers.mount_worker.mount_receiver_handler
        else:
            if user_id not in get_instance_calls:
                get_instance_calls[user_id] = []
            get_instance_calls[user_id].append(
                (subflow_key, subflow_endpoint, subflow_config_overrides)
            )

    if len(get_instance_calls) > 0:
        get_instances_results.update(
            _get_remote_flow_instances(cl=cl, get_instance_calls=get_instance_calls)
        )

    return get_instances_results


def _get_local_flow_instance(
    cl: CoLink,
    client_id: str,
    flow_endpoint: str,
    config_overrides: Dict[str, Any] = {},
    initial_state: Dict[str, Any] = None,
    dispatch_point_override: str = None,
) -> str:
    """
    Gets an instance of a flow being served at flow_endpoint. Returns id of the flow instance.
    Throws FlowInstanceException.

    :param cl:
    :type cl: CoLink
    :param client_id:
    :type client_id: str
    :param config_overrides:
    :type config_overrides: Dict[str, Any]
    :param initial_state:
    :type initial_state: Dict[str, Any]
    :param dispatch_point_override: overrides dispatch point for this instance (only relevant for locally served flows)
    :type dispatch_point_override: Dict[str, Any]
    :return: flow instance id
    :rtype: str
    """
    if not is_flow_served(cl, flow_endpoint):
        raise FlowInstanceException(
            flow_endpoint=flow_endpoint,
            user_id=cl.get_user_id(),
            message=f"Not serving at {flow_endpoint}.",
        )

    serve_entry_path = f"{COFLOWS_PATH}:{flow_endpoint}"
    is_singleton = coflows_deserialize(cl.read_entry(f"{serve_entry_path}:singleton"))

    if is_singleton:
        # return first mount that has init = 1
        client_keys = cl.read_keys(
            prefix=f"{cl.get_user_id()}::{serve_entry_path}:mounts",
            include_history=False,
        )
        for client_key in client_keys:
            client_id_full_path = str(client_key.key_path).split("@")[0]
            client_id = str(client_key.key_path).split("@")[0].split(":")[-1]
            instance_keys = cl.read_keys(
                prefix=client_id_full_path,
                include_history=False,
            )
            for instance_key in instance_keys:
                instance_id = str(instance_key.key_path).split("@")[0].split(":")[-1]
                instance_init = coflows_deserialize(
                    cl.read_entry(
                        f"{serve_entry_path}:mounts:{client_id}:{instance_id}:init"
                    )
                )
                if instance_init == 1:
                    print("Fetched singleton", instance_id)
                    return instance_id

    # recursively create new instance
    flow_class_name = coflows_deserialize(
        cl.read_entry(f"{serve_entry_path}:flow_class_name")
    )
    if flow_class_name is None:
        raise FlowInstanceException(
            flow_endpoint=flow_endpoint,
            user_id=cl.get_user_id(),
            message=f"flow class name {flow_class_name} not found at {serve_entry_path}",
        )

    flow_class = hydra.utils.get_class(flow_class_name)
    config = flow_class.get_config(**deepcopy(config_overrides))

    # TODO should this be done here? probably NO - should be done in run.py
    api_info = [ApiInfo(backend_used="openai", api_key=os.getenv("OPENAI_API_KEY"))]
    quick_load_api_keys(config, api_info, key="api_infos")

    # TODO create flow object and store its pickle
    # flow_obj = flow_class.instantiate_from_default_config(cl, config_overrides)
    # flow_obj.mount() # pickles itself and saves to storage
    # return flow_obj.get_instance_id()

    # TODO this can be carefully moved to CompositeFlow._set_up_subflows()
    if "subflows_config" in config:
        get_instances_results = _get_collaborative_subflow_instances(
            cl, client_id, config["subflows_config"]
        )
        # also check aiflows.workers.mount_worker.mount_receiver_handler

        for subflow_key, get_instance_result in get_instances_results.items():
            if get_instance_result["successful"] is False:
                message = get_instance_result["message"]
                raise FlowInstanceException(
                    flow_endpoint=flow_endpoint,
                    user_id=cl.get_user_id(),
                    message=f"Failed to get instance of subflow {subflow_key}.\n{message}",
                )

            config["subflows_config"][subflow_key][
                "_target_"
            ] = "aiflows.base_flows.AtomicFlow.instantiate_from_default_config"
            config["subflows_config"][subflow_key]["flow_id"] = get_instance_result[
                "flow_id"
            ]

    # print("Creating new flow instance with config:\n", json.dumps(config, indent=4))
    flow_id = mount(
        cl,
        client_id,
        flow_endpoint,
        config,
        initial_state,
        dispatch_point_override,
    )

    return str(flow_id)


def get_flow_instance(
    cl: CoLink,
    flow_endpoint: str,
    user_id: str = "local",
    config_overrides: Dict[str, Any] = {},
    initial_state: Dict[str, Any] = None,
    dispatch_point_override: str = None,
) -> AtomicFlow:
    """
    Returns an atomic flow wrapper around an instance of the specified flow.

    :param flow_endpoint:
    :type flow_endpoint: str
    :param user_id:
    :type user_id: str
    :param config_overrides:
    :type config_overrides: Dict[str, Any]
    :param initial_state:
    :type initial_state: Dict[str, Any]
    :param dispatch_point_override: overrides dispatch point for this instance (only relevant for locally served flows)
    :type dispatch_point_override: Dict[str, Any]
    :return: atomic flow wrapper around flow instance
    :rtype: aiflows.base_flows.AtomicFlow
    """
    user_id = "local" if user_id == cl.get_user_id() else user_id
    try:
        if user_id == "local":
            flow_id = _get_local_flow_instance(
                cl=cl,
                client_id="local",
                flow_endpoint=flow_endpoint,
                config_overrides=config_overrides,
                initial_state=initial_state,
                dispatch_point_override=dispatch_point_override,
            )
        else:
            get_results = _get_remote_flow_instances(
                cl=cl,
                get_instance_calls={
                    user_id: [("my_flow", flow_endpoint, config_overrides)]
                },
            )["my_flow"]
            if get_results["successful"] is False:
                raise FlowInstanceException(
                    flow_endpoint=flow_endpoint,
                    user_id=user_id,
                    message=get_results["message"],
                )
            flow_id = get_results["flow_id"]
    except grpc.RpcError as e:
        raise FlowInstanceException(
            flow_endpoint,
            user_id,
            message=f"Received RPC exception: code={e.code()} message={e.details()}",
        )

    proxy_overrides = {
        "name": f"Proxy_{flow_endpoint}",
        "description": f"Proxy of {flow_endpoint}",
        "user_id": user_id,
        "flow_id": str(flow_id),
        "flow_endpoint": flow_endpoint,
    }
    proxy_flow = AtomicFlow.instantiate_from_default_config(**proxy_overrides)
    proxy_flow.set_colink(cl)

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


# def serve_flow(
#     cl: CoLink,
#     flow_type: str,
#     default_config: Dict[str, Any] = None,
#     default_state: Dict[str, Any] = None,
#     default_dispatch_point: str = DEFAULT_DISPATCH_POINT,
#     singleton: bool = False,
#     parallel_dispatch: bool = False,
# ) -> bool:
#     """
#     Serves the flow config under the identifier flow_type.
#     After serving, users can get an instance of the served flow via the get_instance operation.

#     :return: True if the flow was successfully served; False if the flow is already served or an error occurred.
#     :rtype: bool
#     """
#     serve_entry_path = f"{COFLOWS_PATH}:{flow_type}"

#     if is_flow_served(cl, flow_type):
#         print(f"{flow_type} is already being served at {serve_entry_path}")
#         return False

#     # if dispatch_mode not in DISPATCH_MODES:
#     #     print(
#     #         f"Invalid dispatch_mode '{dispatch_mode}'. Use one of {', '.join(DISPATCH_MODES)}"
#     #     )
#     #     return False

#     # NOTE depricating for now
#     # if default_state is None and default_config is not None:
#     #     default_state = default_config.get("init_state", None)

#     # serve
#     try:
#         cl.update_entry(f"{serve_entry_path}:init", coflows_serialize(1))
#         cl.update_entry(
#             f"{serve_entry_path}:default_dispatch_point",
#             default_dispatch_point,
#         )
#         cl.update_entry(
#             f"{serve_entry_path}:parallel_dispatch",
#             coflows_serialize(parallel_dispatch),
#         )

#         if default_config is not None:
#             # TODO what if target is not given
#             target = default_config["_target_"]
#             if target.split(".")[-1] in INSTANTIATION_METHODS:
#                 target = ".".join(target.split(".")[:-1])

#             flow_class = hydra.utils.get_class(target)
#             default_config = flow_class.get_config(**deepcopy(default_config))
#             cl.update_entry(
#                 f"{serve_entry_path}:default_config",
#                 coflows_serialize(default_config),
#             )

#         if default_state is not None:
#             cl.update_entry(
#                 f"{serve_entry_path}:default_state",
#                 coflows_serialize(default_state, use_pickle=True),
#             )

#         # if serve_mode == "stateless":
#         #     flow_id = f"{flow_type}_stateless"
#         #     instance_metadata = {
#         #         "flow_type": flow_type,
#         #         "user_id": "local",
#         #         "serve_mode": "stateless",
#         #     }
#         #     cl.create_entry(
#         #         f"{INSTANCE_METADATA_PATH}:{flow_id}",
#         #         coflows_serialize(instance_metadata),
#         #     )

#     except grpc.RpcError:
#         return False

#     print(f"Started serving at {serve_entry_path}.")
#     return True


# def recursive_serve_flow(
#     cl: CoLink,
#     flow_type: str,
#     serving_mode="statefull",
#     default_config: Dict[str, Any] = None,
#     default_state: Dict[str, Any] = None,
#     default_dispatch_point: str = None,
# ) -> bool:
#     # expand default config to full default_config

#     # ugly hack to get class but not sure how else to do if
#     target = default_config["_target_"]

#     if target.split(".")[-1] in INSTANTIATION_METHODS:
#         target = ".".join(target.split(".")[:-1])

#     flow_class = hydra.utils.get_class(target)
#     flow_full_config = flow_class.get_config(**deepcopy(default_config))

#     # if there's recursive serving, serve subflows first
#     if "subflows_config" in flow_full_config:
#         for subflow, subflow_config in flow_full_config["subflows_config"].items():
#             # A flow is proxy if it's type is AtomicFlow or Flow (since no run method is implemented in these classes)
#             # TODO: Check if this is sufficient

#             needs_serving = subflow_config.get("user_id", "local") == "local"
#             # if the flow is not a proxy, we must serve it and then make it become a proxy in the default_config
#             if needs_serving:
#                 # This is ok because name is a required field in the config
#                 # note that if you don't specify the flow type, I'll assume it's the name of the subflow + _served
#                 # This means that if you don't specify the flow type, 2 subflows of the same class will be served at 2 different locations (won't share state)
#                 # If you want to share state, you must specify the flow type
#                 subflow_type = subflow_config.get("flow_type", f"{subflow}_served")
#                 subflow_default_state = subflow_config.get("init_state", None)
#                 # serve_flow returns false when an error occurs or if a flow is already served... (shouldn't we distinguish these cases?)
#                 # I would almost fail here if the error here
#                 # whereas if the flow is already serving that's great, nothing to be done
#                 # Which is why I called the output serving succesful

#                 subflow_target = subflow_config["_target_"]

#                 if subflow_target.split(".")[-1] in INSTANTIATION_METHODS:
#                     subflow_target = ".".join(subflow_target.split(".")[:-1])

#                 subflow_class = hydra.utils.get_class(subflow_target)

#                 # Mauro suggestion: serve the default configuration all the time for subflows (mount overrieds stuff)
#                 subflow_cfg = subflow_class.get_config()
#                 subflow_cfg["_target_"] = subflow_config["_target_"]
#                 serving_succesful = recursive_serve_flow(
#                     cl=cl,
#                     flow_type=subflow_type,
#                     # TODO: shouldn't this be read from yaml file of subflow (find it in flow_modules directory)
#                     default_config=subflow_cfg,
#                     default_state=subflow_default_state,
#                     default_dispatch_point=default_dispatch_point,
#                 )

#                 # Change the subflow_config of flow to proxy
#                 # Quite ugly, but what am I supposed to do?

#                 if subflow not in default_config["subflows_config"]:
#                     default_config["subflows_config"][subflow] = {}

#                 default_config["subflows_config"][subflow][
#                     "_target_"
#                 ] = f"aiflows.base_flows.AtomicFlow.instantiate_from_default_config"
#                 default_config["subflows_config"][subflow]["user_id"] = "local"
#                 default_config["subflows_config"][subflow]["flow_type"] = subflow_type
#                 if "name" not in default_config["subflows_config"][subflow]:
#                     default_config["subflows_config"][subflow]["name"] = subflow_cfg[
#                         "name"
#                     ]
#                 if "description" not in subflow_config:
#                     default_config["subflows_config"][subflow][
#                         "description"
#                     ] = subflow_cfg["description"]

#     serving_succesful = serve_flow(
#         cl=cl,
#         flow_type=flow_type,
#         serving_mode=serving_mode,
#         default_config=default_config,
#         default_state=default_state,
#         default_dispatch_point=default_dispatch_point,
#     )
#     return serving_succesful
