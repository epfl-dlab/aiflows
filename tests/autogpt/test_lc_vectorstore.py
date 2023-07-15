import os
from flows.application_flows.VectorStoreFlow import VectorStoreFlow

def test_vec():
    mem_flow = VectorStoreFlow.instantiate_from_default_config()
    print(mem_flow)
    
    input_message = mem_flow.package_input_message(
        {"operation": "write", "content": ["hello world", "bye world"]},
        api_keys={
            "openai": "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"
        }
    )
    print(mem_flow(input_message))

    input_message = mem_flow.package_input_message(
        {"operation": "write", "content": ["hello world", "bye world"]},
        api_keys={
            "openai": "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"
        }
    )
    print(mem_flow(input_message))