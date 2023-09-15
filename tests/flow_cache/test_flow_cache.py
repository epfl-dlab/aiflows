import os
import mock
import pytest
from typing import Any, Dict, List, Optional, MutableMapping

from flows.base_flows import AtomicFlow
from flows.flow_cache import clear_cache, CACHING_PARAMETERS, FlowCache
from flows.utils.general_helpers import flatten_dict
from flows.data_transformations import KeyRename
from flows.utils.logging import set_verbosity_debug


class EchoFlow(AtomicFlow):
    SUPPORTS_CACHING = True

    __default_flow_config = {
        "input_keys": ["user_input"]
    }

    def run(self,
            input_data: Dict[str, Any]) -> Dict[str, Any]:
        
        user_input = input_data["user_input"]
        return {"echo": user_input}

class EchoFlowNoCache(EchoFlow):
    SUPPORTS_CACHING = False

    def run(self,
            input_data: Dict[str, Any]) -> Dict[str, Any]:
        return super().run(input_data=input_data)

@pytest.fixture(autouse=True)
def reset_cache():
    clear_cache()
    yield None
    clear_cache()

@pytest.fixture
def enable_cache_globally():
    CACHING_PARAMETERS.do_caching = True

@pytest.fixture
def disable_cache_globally():
    CACHING_PARAMETERS.do_caching = False

def test_enable_cache_globally(enable_cache_globally):
    # set_verbosity_debug()
    
    echo_flow = EchoFlow.instantiate_from_default_config({
        "name": "EchoFlow",
        "description": "EchoFlow",
        "input_keys": ["user_input"],
        "enable_cache": True
    })
    assert(len(echo_flow.cache)) == 0

    # print(echo_flow)
    input_message = echo_flow.package_input_message(
        {"user_input": "hello"}
    )
    output_message = echo_flow(input_message)
    # print(output_message)
    assert len(echo_flow.cache) > 0

def test_enable_cache_globally_disable_flow_wise(enable_cache_globally):
    echo_flow = EchoFlow.instantiate_from_default_config({
        "name": "EchoFlow",
        "description": "EchoFlow",
        "enable_cache": False,
    })
    assert len(echo_flow.cache) == 0
    print(echo_flow)

    input_message = echo_flow.package_input_message(
        {"user_input": "hello"}
    )
    output_message = echo_flow(input_message)

    assert len(echo_flow.cache) == 0

def test_enable_cache_globally_flow_not_support_cache(enable_cache_globally):
    echo_flow = EchoFlowNoCache.instantiate_from_default_config({
        "name": "EchoFlow",
        "description": "EchoFlow",
        "enable_cache": True
    })
    assert len(echo_flow.cache) == 0

    input_message = echo_flow.package_input_message(
        {"user_input": "hello"}
    )
    try:
        output_message = echo_flow(input_message)
    except:
        assert len(echo_flow.cache) == 0
        return
    
    assert False, "Should have raised an exception"



def test_disable_cache_globally(disable_cache_globally):

    echo_flow = EchoFlow.instantiate_from_default_config({
        "name": "EchoFlow",
        "description": "EchoFlow",
        "input_keys": ["user_input"],
        "enable_cache": True
        # "output_keys": ["echo"],
    })
    assert len(echo_flow.cache) == 0
    # print(echo_flow)
    input_message = echo_flow.package_input_message(
        {"user_input": "hello"}
    )
    output_message = echo_flow(input_message)

    # print(output_message)
    assert len(echo_flow.cache) == 0

