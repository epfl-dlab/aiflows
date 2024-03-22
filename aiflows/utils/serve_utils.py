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
from aiflows.utils import logging

log = logging.get_logger(__name__)


class FlowInstanceException(Exception):
    def __init__(self, flow_endpoint, user_id, message=""):
        self.flow_endpoint = (flow_endpoint,)
        self.user_id = user_id
        self.message = f"Failed to get flow instance at {flow_endpoint} served by user {user_id}.\nMessage: {message}"
        super().__init__(self.message)


def is_flow_served(cl: CoLink, flow_endpoint: str) -> bool:
    """Returns True if the flow is being served at the given endpoint.

    :param cl: colink object
    :type cl: CoLink
    :param flow_endpoint: endpoint of the flow
    :type flow_endpoint: str
    :return: True if the flow is being served at the given endpoint
    :rtype: bool
    """
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

    :param cl: colink object
    :type cl: CoLink
    :param flow_class_name: name of the flow class (e.g. "aiflows.base_flows.AtomicFlow" or "flow_modules.my_flow.MyFlow")
    :type flow_class_name: str
    :param flow_endpoint: endpoint of the flow (the name under which the flow will be served). Users will use this endpoint to get instances of the flow.
    :type flow_endpoint: str
    :param dispatch_point: dispatch point for the flow
    :type dispatch_point: str
    :param parallel_dispatch: whether to use parallel dispatch for the flow. If True, multiple calls to the same flow instance can be done simultaneously (the flow is stateless).
    :type parallel_dispatch: bool
    :param singleton: whether to serve the flow as a singleton. If True, only one instance of the flow can be mounted. Users will all get the same instance.
    :return: True if the flow was successfully served; False if the flow is already served or an error occurred.
    :rtype: bool
    """
    serve_entry_path = f"{COFLOWS_PATH}:{flow_endpoint}"
    if is_flow_served(cl, flow_endpoint):
        log.info(f"Already serving at {serve_entry_path}")
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
        log.info(f"Received RPC exception: code={e.code()} message={e.details()}")
        return False

    log.info(f"Started serving {flow_class_name} at {serve_entry_path}.")
    log.info(f"dispatch_point: {dispatch_point}")
    log.info(f"parallel_dispatch: {parallel_dispatch}")
    log.info(f"singleton: {singleton}\n")
    return True


def delete_flow_endpoint(cl: CoLink, flow_endpoint: str):
    """Deletes all colink entries at given flow_endpoint. This includes deleting all instances of this flow.

    :param cl: colink object
    :type cl: CoLink
    :param flow_endpoint: endpoint of the flow
    :type flow_endpoint: str
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
                    log.info(f"Deleted flow instance {instance_id}")
                    # TODO delete mailbox in scheduler
                except grpc.RpcError:
                    log.info(
                        f"WARNING: flow {instance_id} is mounted but it's metadata doesn't exist."
                    )
                    continue

        colink_utils.delete_entries_on_path(cl, serve_entry_path)
        log.info(f"Stopped serving at {serve_entry_path}")
    except grpc.RpcError as e:
        log.info(f"Received RPC exception: code={e.code()} message={e.details()}")


def delete_all_flow_endpoints(cl: CoLink):
    """Deletes all flow endpoints. This includes deleting all flow instances.

    :param cl: colink object
    :type cl: CoLink
    """
    flow_endpoints = cl.read_keys(
        prefix=f"{cl.get_user_id()}::{COFLOWS_PATH}",
        include_history=False,
    )
    for flow_endpoint_key in flow_endpoints:
        flow_endpoint = (
            str(flow_endpoint_key).split("::")[1].split("@")[0].split(":")[-1]
        )
        delete_flow_endpoint(cl, flow_endpoint)


def unserve_flow(cl: CoLink, flow_endpoint: str):
    """unserves flow - users will no longer be able to get instances from this flow_endpoint. all live instances created on this flow_endpoint remain alive.

    :param cl: colink object
    :type cl: CoLink
    :param flow_endpoint: endpoint of the flow
    :type flow_endpoint: str
    """
    if not is_flow_served(cl, flow_endpoint):
        log.info(f"{flow_endpoint} wasn't being served.")
        return

    serve_entry_path = f"{COFLOWS_PATH}:{flow_endpoint}"
    try:
        cl.update_entry(f"{serve_entry_path}:init", coflows_serialize(0))
    except grpc.RpcError as e:
        log.info(f"Received RPC exception: code={e.code()} message={e.details()}")
        return

    log.info(f"Stopped serving at {serve_entry_path}")


def _get_local_flow_instance_metadata(cl: CoLink, flow_id: str):
    """Returns dict with metadata about specified local flow instance. This includes flow_endpoint and client_id.

    :param cl: colink object
    :type cl: CoLink
    :param flow_id: id of the flow instance
    :type flow_id: str
    :return: dict with metadata about specified local flow instance
    :rtype: Dict[str, Any]
    """
    instance_metadata = coflows_deserialize(
        cl.read_entry(f"{INSTANCE_METADATA_PATH}:{flow_id}")
    )
    return instance_metadata


def delete_flow_instance(cl: CoLink, flow_id: str):
    """Deletes all colink entries associated with flow instance.

    :param cl: colink object
    :type cl: CoLink
    :param flow_id: id of the flow instance
    :type flow_id: str
    :return: dict with metadata about specified local flow instance
    :rtype: Dict[str, Any]
    """
    instance_metadata = _get_local_flow_instance_metadata(cl, flow_id)
    if instance_metadata is None:
        log.info(f"Metadata for {flow_id} doesn't exist.")
        return
    flow_endpoint = instance_metadata["flow_endpoint"]
    client_id = instance_metadata["user_id"]
    client_id = "local" if client_id == cl.get_user_id() else client_id

    serve_entry_path = f"{COFLOWS_PATH}:{flow_endpoint}"
    mount_path = f"{serve_entry_path}:mounts:{client_id}:{flow_id}"
    metadata_path = f"{INSTANCE_METADATA_PATH}:{flow_id}"

    colink_utils.delete_entries_on_path(cl, mount_path)
    colink_utils.delete_entries_on_path(cl, metadata_path)
    log.info(f"Deleted flow instance {flow_id}.")
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
    """Mounts a new instance at the specified flow endpoint by creating necessary entries in CoLink storage.

    :param cl: colink object
    :type cl: CoLink
    :param client_id: id of colink user making the request (also known as user_id)
    :type client_id: str
    :param flow_endpoint: endpoint of the flow
    :type flow_endpoint: str
    :param config_overrides: dictionary with config overrides for the flow instance
    :type config_overrides: Dict[str, Any]
    :param initial_state: initial state of the flow instance
    :type initial_state: Dict[str, Any]
    :param dispatch_point_override: overrides dispatch point for this instance
    :type dispatch_point_override: Dict[str, Any]

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

    log.info(f"Mounted {flow_id} at {mount_path}")

    return flow_id


def _get_remote_flow_instances(
    cl: CoLink,
    get_instance_calls,  # user_id --> List((flow_key, flow_endpoint, cfg_overrides))
) -> Dict[str, Any]:
    """Gets instances of specified flows. User specifies flows by passing

    :param cl: colink object
    :type cl: CoLink
    :param get_instance_calls: dictionary mapping user ids to lists of tuples (flow_key, flow_endpoint, cfg_overrides)
    :type get_instance_calls: Dict[str, List[Tuple[str, str, Dict[str, Any]]]]
    :return: dictionary mapping flow keys to flow ids
    """
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
            # already have instance
            continue

        if "user_id" not in subflow_config:
            get_instances_results[subflow_key] = {
                "flow_id": "",
                "successful": False,
                "message": f"Subflow {subflow_key} missing user_id in config.",
            }
            continue

        if "flow_endpoint" not in subflow_config:
            get_instances_results[subflow_key] = {
                "flow_id": "",
                "successful": False,
                "message": f"Subflow {subflow_key} missing flow_endpoint in config.",
            }
            continue

        user_id = subflow_config["user_id"]
        user_id = "local" if user_id == cl.get_user_id() else user_id
        subflow_endpoint = subflow_config["flow_endpoint"]

        subflow_config_overrides = deepcopy(subflow_config)
        # TODO should we remove this?
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
                    log.info(f"Fetched singleton {instance_id}")
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
    log.info(
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
    log.info(colored(f"{component_name}\n", "grey", attrs=["bold"]))

    log.info(colored(json.dumps(args, indent=4), "white"))
    log.info("\n")

    log.info("Connecting to colink server...")
    cl = CoLink(args["addr"], args["jwt"])
    log.info(f"Connected to {cl.get_core_addr()} as user {cl.get_user_id()}\n")
    return cl


def recursive_serve_flow(
    cl: CoLink,
    flow_class_name: str,
    flow_endpoint: str,
    dispatch_point: str = DEFAULT_DISPATCH_POINT,
    parallel_dispatch: bool = False,
    singleton: bool = False,
) -> bool:
    flow_class = hydra.utils.get_class(flow_class_name)
    flow_config = flow_class.get_config()

    if "subflows_config" in flow_config:
        for subflow, subflow_config in flow_config["subflows_config"].items():
            needs_serving = subflow_config.get("user_id", "local") == "local"
            if not needs_serving:
                continue

            subflow_endpoint = subflow_config.get("flow_endpoint", None)
            if subflow_endpoint is None:
                log.info(
                    f"Failed to serve subflow {subflow}: missing subflow_endpoint in config."
                )
                return False
            if is_flow_served(cl, subflow_endpoint):
                log.info(f"Subflow {subflow} already served.")
                continue

            subflow_class_name = subflow_config.get("flow_class_name", None)
            if subflow_class_name is None:
                log.info(
                    f"Failed to serve subflow {subflow}: missing flow_class_name in config."
                )
                return False

            subflow_dispatch_point = subflow_config.get(
                "dispatch_point", DEFAULT_DISPATCH_POINT
            )
            subflow_parallel_dispatch = subflow_config.get("parallel_dispatch", False)
            subflow_singleton = subflow_config.get("singleton", False)

            subflow_served = recursive_serve_flow(
                cl,
                subflow_class_name,
                subflow_endpoint,
                subflow_dispatch_point,
                subflow_parallel_dispatch,
                subflow_singleton,
            )
            if not subflow_served:
                log.info(f"Failed to serve subflow {subflow}.")
                return False

    return serve_flow(
        cl, flow_class_name, flow_endpoint, dispatch_point, parallel_dispatch, singleton
    )
