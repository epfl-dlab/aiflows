import functools
import os
import hashlib
import threading
from dataclasses import dataclass
from typing import Dict, List
import copy
from diskcache import Index

from flows.base_flows.abstract import AtomicFlow

# ToDo: Implement loading

@dataclass
class CACHING_PARAMETERS:
    # Global parameters that can be set before starting the outer-flow
    max_cached_entries: int = 1000
    do_caching: bool = True
    cache_dir: str = None


@dataclass
class CachingValue:
    output_results: Dict
    full_state: Dict


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
    assert flow, "Could not check in the cache because the flow was not given"

    return flow


def _custom_hash(all_args):
    _repr_args = [repr(arg) for arg in all_args]
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
            all_args = list(args) + list(kwargs.values())

            flow = get_calling_flow(all_args)
            assert isinstance(flow, AtomicFlow), "Caching is only supported for AtomicFlows."
            input_data = kwargs["input_data"]
            expected_outputs = kwargs["expected_outputs"]

            key = _custom_hash([flow, input_data, expected_outputs])

            # Check if the key is already in the cache
            with lock:
                if key in cache:
                    # Custom retrieval behavior
                    cached_value: CachingValue = cache[key]
                    result = cached_value.output_results
                    # ToDo: Update how to load the full_state when instantiate / config / __setstate__ roles are clarified
                    flow.__setstate__(cached_value.full_state)

                    print(f"Retrieved from cache: {flow.__class__.__name__} "
                          f"-- {method.__name__}(input_data.keys()={list(input_data.keys())}, expected_outputs={expected_outputs})")
                    print("Retrieved from cache:", cached_value)
                else:
                    # Call the original function
                    result = method(*args, **kwargs)

                    value_to_cache = CachingValue(
                        output_results=result,
                        # ToDo: Update full_state param when instantiate / config / __setstate__ roles are clarified
                        full_state=copy.deepcopy(flow.__getstate__())
                    )

                    cache[key] = value_to_cache
                    print("Cached:", value_to_cache)

            return result

        def clear_cache():
            with lock:
                print("Cache clearing")
                cache.clear()

        wrapper.clear_cache = clear_cache
        return wrapper

    return decorator
