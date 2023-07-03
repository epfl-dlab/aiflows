import functools
import os
import hashlib
import threading
from dataclasses import dataclass
from typing import Dict, List
import copy
from diskcache import Index

# ToDo: Add logging


@dataclass
class CACHING_PARAMETERS:
    # ToDo: Expose these params in the launcher (and the configs when available)
    #   The params should be updated before the library is loaded. Make sure to do this reliably.
    #   How to do this in a clean way?
    # ToDo: Add support for infinite cache if we intend to use it for resuming/extending runs.
    #   Is that even a good idea?
    #   What happens if you want to resume/extend a run that has been already resumed/extended?
    # Global parameters that can be set before starting the outer-flow
    max_cached_entries: int = 1000
    do_caching: bool = True
    cache_dir: str = None


@dataclass
class CachingValue:
    output_results: Dict
    full_state: Dict
    history_messages_created: List


def get_cache_dir() -> str:
    cache_dir = CACHING_PARAMETERS.cache_dir
    if cache_dir:
        return os.path.join(cache_dir)

    current_dir = os.getcwd()
    return os.path.abspath(os.path.join(current_dir, '.flow_cache'))


def get_calling_flow(all_args: List):
    from flows.base_flows import Flow

    flow = None
    for arg in all_args:
        if isinstance(arg, Flow):
            flow = arg
    assert flow, "Couldn't identify the flow corresponding to the run call."

    return flow


def _custom_hash(all_args):
    _repr_args = []
    for arg in all_args:
        _repr_args.append(repr(arg))
    return hashlib.sha256(repr(_repr_args).encode("utf-8")).hexdigest()


def flow_run_cache():
    if not CACHING_PARAMETERS.do_caching:
        def no_decorator(method):
            return method

        return no_decorator

    def decorator(method):
        cache_dir = get_cache_dir()
        cache = Index(cache_dir)
        lock = threading.Lock()

        @functools.wraps(method)
        def wrapper(*args, **kwargs):
            # Check how API_keys are handles
            all_args = list(args) + list(kwargs.values())

            flow = get_calling_flow(all_args)
            if not flow.SUPPORTS_CACHING:
                raise Exception(f"Flow {flow.__class__.__name__} does not support caching")

            input_data = kwargs["input_data"]
            keys_to_ignore_for_hash = kwargs["keys_to_ignore_for_hash"]
            input_data_to_hash = {k: v for k, v in input_data.items() if k not in keys_to_ignore_for_hash}
            key = _custom_hash([flow, input_data_to_hash, keys_to_ignore_for_hash])

            # Check if the key is already in the cache
            with lock:
                if key in cache:
                    # Custom retrieval behavior
                    cached_value: CachingValue = cache[key]

                    # Retrieve output from cache
                    result = cached_value.output_results

                    # Restore the flow to the state it was in when the output was created
                    flow.__setstate__(cached_value.full_state)

                    # Restore the history messages
                    for message in cached_value.history_messages_created:
                        message_softcopy = message  # ToDo: Get a softcopy with an updated timestamp
                        flow._log_message(message_softcopy)

                    # TODO(yeeef): use log.debug
                    # print(f"Retrieved from cache: {flow.__class__.__name__} "
                    #       f"-- {method.__name__}(input_data.keys()={list(input_data_to_hash.keys())}, "
                    #       f"keys_to_ignore_for_hash={keys_to_ignore_for_hash})")
                    # print("Retrieved from cache:", cached_value)
                else:
                    # Call the original function
                    history_len_pre_execution = len(flow.history)

                    # Execute the call
                    result = method(*args, **kwargs)

                    # Retrieve the messages created during the execution
                    num_created_messages = len(flow.history) - history_len_pre_execution
                    new_history_messages = flow.history.get_last_n_messages(num_created_messages)

                    value_to_cache = CachingValue(
                        output_results=result,
                        full_state=flow.__getstate__(),
                        history_messages_created=new_history_messages
                    )

                    cache[key] = value_to_cache
                    # print("Cached:", value_to_cache)

            return result

        def clear_cache():
            with lock:
                print("Cache clearing")
                cache.clear()

        wrapper.clear_cache = clear_cache
        return wrapper

    return decorator


def clear_cache():
    cache_dir = get_cache_dir()
    cache = Index(cache_dir)
    cache.clear()
