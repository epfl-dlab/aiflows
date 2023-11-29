from flows.base_flows import Flow
from typing import List, Dict, Any


class MockChatOpenAI:
    def __init__(self, num_fails=2, *args, **kwargs):
        self.fail_count = 0
        self.num_fails = num_fails

    def __call__(self, *args, **kwargs):
        if self.fail_count < self.num_fails:
            self.fail_count += 1
            raise Exception("mockery")
        else:
            return MockResponse()


current_time = 0


def increment_time():
    global current_time
    current_time += 1
    return current_time


class MockBrokenChatOpenAI:
    def __init__(self, *args, **kwargs):
        pass

    def __call__(self, *args, **kwargs):
        raise Exception("mockery")


class MockResponse:
    def __init__(self):
        self.content = "hello"


def create_mock_data(num_samples):
    return [[{"id": idx, "query": f"query {idx}"}] for idx in range(num_samples)]


class MockAnnotator:
    def __init__(self, key, *args, **kwargs):
        self.key = key

    def __call__(self, data, *args, **kwargs):
        return {self.key: data}


class MockMessage:
    pass


class MockFlow(Flow):
    def __init__(self, name="test", description="description", **kwargs):
        super().__init__(name=name, description=description, **kwargs)

    def run(self, input_data: Dict[str, Any], output_keys: List[str]) -> Dict[str, Any]:
        return {"inference_outputs": "test", "mock_flow_api_key": self.flow_state["api_key"]}


class BrokenMockFlow(Flow):
    def __init__(self, name="test", description="description", **kwargs):
        super().__init__(name=name, description=description, **kwargs)

    def run(self, input_data: Dict[str, Any], output_keys: List[str]) -> Dict[str, Any]:
        raise Exception("Test exception")
