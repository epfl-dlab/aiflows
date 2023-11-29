import os
from flows.application_flows.VectorStoreFlowModule import VectorStoreFlow


def test_vec():
    mem_flow = VectorStoreFlow.instantiate_from_default_config(
        {"api_keys": {"openai": "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"}, "keep_raw_response": False}
    )
    print(mem_flow)

    input_message = mem_flow.package_input_message(
        {"operation": "write", "content": ["hello world", "bye world"]},
    )
    output_message = mem_flow(input_message)
    assert output_message.data["output_data"]["retrieved"] == ""

    input_message = mem_flow.package_input_message(
        {"operation": "read", "content": "world"},
    )
    output_message = mem_flow(input_message)
    assert output_message.data["output_data"]["retrieved"] == ["hello world", "bye world"]


if __name__ == "__main__":
    test_vec()
