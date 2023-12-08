import os
import hashlib
import threading
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from diskcache import Index
from aiflows.utils import logging

log = logging.get_logger(__name__)


@dataclass
class CACHING_PARAMETERS:
    """This class contains the global caching parameters.

    :param max_cached_entries: The maximum number of cached entries
    :type max_cached_entries: int, optional
    :param do_caching: Whether to do caching
    :type do_caching: bool, optional
    :param cache_dir: The cache directory
    :type cache_dir: str, optional
    """

    # Global parameters that can be set before starting the outer-flow
    max_cached_entries: int = 10000
    do_caching: bool = True
    cache_dir: str = None


CACHING_PARAMETERS.do_caching = os.getenv("FLOW_DISABLE_CACHE", "false").lower() == "false"


@dataclass
class CachingValue:
    """This class contains the cached value.

    :param output_results: The output results
    :type output_results: Dict
    :param full_state: The full state
    :type full_state: Dict
    :param history_messages_created: The history messages created
    :type history_messages_created: List
    """

    output_results: Dict
    full_state: Dict
    history_messages_created: List


@dataclass
class CachingKey:
    """This class contains the caching key.

    :param flow: The flow
    :type flow: Flow
    :param input_data: The input data
    :type input_data: Dict
    :param keys_to_ignore_for_hash: The keys to ignore for the hash
    :type keys_to_ignore_for_hash: List
    """

    flow: "Flow"
    input_data: Dict[str, Any]
    keys_to_ignore_for_hash: List[str]

    def hash_string(self) -> str:
        return _custom_hash(self.flow, self.input_data, self.keys_to_ignore_for_hash)


def get_cache_dir() -> str:
    """Returns the cache directory.

    :return: The cache directory
    :rtype: str
    """
    cache_dir = CACHING_PARAMETERS.cache_dir
    if cache_dir:
        return os.path.join(cache_dir)

    current_dir = os.getcwd()
    return os.path.abspath(os.path.join(current_dir, ".flow_cache"))


def _custom_hash(*all_args):
    """Returns a custom hash for the given arguments.

    :param \*all_args: The arguments
    :type \*all_args: Any
    :return: The custom hash
    :rtype: str
    """
    _repr_args = []
    for arg in all_args:
        _repr_args.append(repr(arg))
    return hashlib.sha256(repr(_repr_args).encode("utf-8")).hexdigest()


class FlowCache:
    """This class is the flow cache.

    :param index: The index
    :type index: Index
    :param \__lock: The lock
    :type \__lock: threading.Lock
    """

    def __init__(self):
        self._index = Index(get_cache_dir())
        self.__lock = threading.Lock()

    def get(self, key: str) -> Optional[CachingValue]:
        """Returns the cached value for the given key.

        :param key: The key
        :type key: str
        :return: The cached value
        :rtype: Optional[CachingValue]
        """
        with self.__lock:
            return self._index.get(key, None)

    def set(self, key: str, value: CachingValue):
        """Sets the cached value for the given key.

        :param key: The key
        :type key: str
        :param value: The cached value
        :type value: CachingValue
        """
        with self.__lock:
            self._index[key] = value

    def pop(self, key: str):
        """Pops the cached value for the given key.

        :param key: The key
        :type key: str
        """
        with self.__lock:
            return self._index.pop(key)

    def __len__(self):
        """Returns the number of cached entries."""
        with self.__lock:
            return len(self._index)


def clear_cache():
    """Clears the cache."""
    cache_dir = get_cache_dir()
    cache = Index(cache_dir)
    cache.clear()
