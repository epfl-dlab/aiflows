import pytest
import mock
from typing import Any, Dict, List, Optional, MutableMapping

from flows.base_flows import AtomicFlow
from flows.utils.caching_utils import flow_run_cache, clear_cache, CACHING_PARAMETERS
from flows.utils.general_helpers import flatten_dict
from flows.data_transformations import KeyRename
from flows.utils.logging import set_verbosity_debug


class EchoFlow(AtomicFlow):
    SUPPORTS_CACHING = True

    # TODO(yeeef): why do we need this decorator at all? just fancier?
    # what if I just want to use fixed_reply flow? but I have to inherit it
    # and add `flow_run_cache` explicitly?
    # and `flow_run_cache` + `SUPPORTS_CACHING` is just redundant information, it only
    # makes sense if someone inherits something?

    # and this decorator just makes things puzzled. Because some parameters are for cache..

    #     REQUIRED_KEYS_CONFIG = ["name", "description", "clear_flow_namespace_on_run_end", "keep_raw_response"]
    # REQUIRED_KEYS_CONSTRUCTOR = ["flow_config", "input_data_transformations", "output_data_transformations"]


    # TODO(yeeef): too many requirements for a flow...
    #              input_data_transformations and output_data_transformations is confused because it is not in the REQUIRED_KEYS_CONFIG
    @flow_run_cache() 
    def run(self,
            *,
            input_data: Dict[str, Any],
            private_keys: Optional[List[str]] = None,
            keys_to_ignore_for_hash: Optional[List[str]] = None,
            enable_cache: bool = False) -> Dict[str, Any]:
        
        user_input = input_data["user_input"]
        return {"echo": user_input}

class EchoFlow2(EchoFlow):
    SUPPORTS_CACHING = False

cache_data = {}

class MockCacheIndex(MutableMapping):
    def __init__(self, _):
        self._data = cache_data

    def __getitem__(self, key):
        return self._data[key]

    def __setitem__(self, key, value):
        self._data[key] = value

    def __delitem__(self, key):
        del self._data[key]

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)

@pytest.fixture(scope="module", autouse=True)
def mock_cache_index():
    with mock.patch("flows.utils.caching_utils.Index", new=MockCacheIndex) as mock_sync:
        yield mock_sync

@pytest.fixture
def enable_cache_globally():
    CACHING_PARAMETERS.do_caching = True

@pytest.fixture
def disable_cache_globally():
    CACHING_PARAMETERS.do_caching = False

@pytest.fixture(autouse=True)
def clear_cache_before_test():
    cache_data.clear()

def test_enable_cache_globally(enable_cache_globally):
    # TODO(Yeeef): instantiate_from_config exposes too many details

    assert len(cache_data) == 0
    echo_flow = EchoFlow.instantiate_from_default_config({
        "name": "EchoFlow",
        "description": "EchoFlow",
        "input_keys": ["user_input"],
        # "output_keys": ["echo"],
    })
    # print(echo_flow)
    input_message = echo_flow.package_input_message(
        {"user_input": "hello"}
    )
    output_message = echo_flow(input_message)
    # print(output_message)
    assert len(cache_data) > 0

def test_enable_cache_globally_disable_flow_wise(enable_cache_globally):
    # set_verbosity_debug()
    CACHING_PARAMETERS.do_caching = False

    assert len(cache_data) == 0
    echo_flow = EchoFlow.instantiate_from_default_config({
        "name": "EchoFlow",
        "description": "EchoFlow",
        "input_keys": ["user_input"],
        # "output_keys": ["echo"],
    })

    input_message = echo_flow.package_input_message(
        {"user_input": "hello"}
    )
    output_message = echo_flow(input_message, enable_cache=False)

    assert len(cache_data) == 0


def test_disable_cache_globally(disable_cache_globally):
    # set_verbosity_debug()
    CACHING_PARAMETERS.do_caching = False

    assert len(cache_data) == 0
    echo_flow = EchoFlow.instantiate_from_default_config({
        "name": "EchoFlow",
        "description": "EchoFlow",
        "input_keys": ["user_input"],
        # "output_keys": ["echo"],
    })
    # print(echo_flow)
    input_message = echo_flow.package_input_message(
        {"user_input": "hello"}
    )
    output_message = echo_flow(input_message)

    input_message = echo_flow.package_input_message(
        {"user_input": "hello"}
    )
    output_message = echo_flow(input_message, enable_cache=True)
    # print(output_message)
    assert len(cache_data) == 0

