import functools
import os
import hashlib
import threading
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
import copy
from diskcache import Index
from ..utils import logging

log = logging.get_logger(__name__)


@dataclass
class CACHING_PARAMETERS:
    # Global parameters that can be set before starting the outer-flow
    max_cached_entries: int = 10000
    do_caching: bool = True
    cache_dir: str = None


CACHING_PARAMETERS.do_caching = os.getenv("FLOW_DISABLE_CACHE", "false").lower() == "false"


@dataclass
class CachingValue:
    output_results: Dict
    full_state: Dict
    history_messages_created: List


@dataclass
class CachingKey:
    flow: str  # ToDo: This is not a string
    input_data: Dict[str, Any]
    keys_to_ignore_for_hash: List[str]

    def hash_string(self) -> str:
        return _custom_hash(self.flow, self.input_data, self.keys_to_ignore_for_hash)


def get_cache_dir() -> str:
    cache_dir = CACHING_PARAMETERS.cache_dir
    if cache_dir:
        return os.path.join(cache_dir)

    current_dir = os.getcwd()
    return os.path.abspath(os.path.join(current_dir, '.flow_cache'))


def _custom_hash(*all_args):
    _repr_args = []
    for arg in all_args:
        _repr_args.append(repr(arg))
    return hashlib.sha256(repr(_repr_args).encode("utf-8")).hexdigest()


class FlowCache:
    def __init__(self):
        self._index = Index(get_cache_dir())
        self.__lock = threading.Lock()

    def get(self, key: str) -> Optional[CachingValue]:
        # key = key.hash_string()
        log.debug("Getting key: %s", key)

        with self.__lock:
            return self._index.get(key, None)

    def set(self, key: str, value: CachingValue):
        # key = key.hash_string()

        with self.__lock:
            self._index[key] = value

    def pop(self, key: CachingKey):
        key = _custom_hash(key.flow, key.input_data, key.keys_to_ignore_for_hash)

        with self.__lock:
            return self._index.pop(key)

    def __len__(self):
        with self.__lock:
            return len(self._index)


def clear_cache():
    cache_dir = get_cache_dir()
    cache = Index(cache_dir)
    cache.clear()
