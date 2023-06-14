import pytest
from flows.base_flows import Flow
from flows.flow_launcher import BaseLauncher, FlowAPILauncher
from torch.utils.data import DataLoader, Dataset
from typing import List, Dict, Any
from collections import defaultdict
from tests.mocks import create_mock_data, increment_time
import time
from tests.mocks import MockFlow, BrokenMockFlow
def test_init_flow_launcher():
    config={
        "api_keys":["key1", "key2"],
    }
    flow = MockFlow(name="test", description="test")
    n_independent_samples = 2
    fault_tolerant_mode = False
    n_batch_retries = 1
    wait_time_between_retries = 1
    expected_outputs=["inference_outputs"]

    FlowAPILauncher(flow, n_independent_samples, fault_tolerant_mode, n_batch_retries, wait_time_between_retries, expected_outputs, **config)

def test_predict(monkeypatch):
    monkeypatch.setattr(time, "sleep", lambda x: None)
    monkeypatch.setattr(time, "time", increment_time)

    num_samples = 10
    data = create_mock_data(num_samples)

    config={
        "api_keys":["key1", "key2"],
    }
    flow = MockFlow(name="test", description="test")
    n_independent_samples = 2
    fault_tolerant_mode = False
    n_batch_retries = 1
    wait_time_between_retries = 1
    expected_outputs=["inference_outputs"]

    launcher = FlowAPILauncher(flow, n_independent_samples, fault_tolerant_mode, n_batch_retries, wait_time_between_retries, expected_outputs, **config)
    results = []
    current_key = None
    for batch in data:
        batch = launcher.predict(batch)
        assert len(batch)==1
        key = batch[0]["api_key"]
        assert key != current_key
        current_key = key
        results.append(batch)


    config={
        "api_keys":["key1", "key2"],
    }
    flow = MockFlow(name="test", description="test")
    n_independent_samples = 2
    fault_tolerant_mode = True
    n_batch_retries = 1
    wait_time_between_retries = 1
    expected_outputs=["inference_outputs"]

    launcher = FlowAPILauncher(flow, n_independent_samples, fault_tolerant_mode, n_batch_retries, wait_time_between_retries, expected_outputs, **config)
    results = []
    current_key = None
    for batch in data:
        batch = launcher.predict(batch)
        assert len(batch)==1
        key = batch[0]["api_key"]
        assert key != current_key
        current_key = key
        results.append(batch)

def test_predict_with_exception(monkeypatch):
    monkeypatch.setattr(time, "sleep", lambda x: None)
    monkeypatch.setattr(time, "time", increment_time)

    num_samples = 10
    data = create_mock_data(num_samples)

    config={
        "api_keys":["key1", "key2"],
    }
    flow = BrokenMockFlow(name="test", description="test")
    n_independent_samples = 2
    fault_tolerant_mode = True
    n_batch_retries = 1
    wait_time_between_retries = 1
    expected_outputs=["inference_outputs"]

    launcher = FlowAPILauncher(flow, n_independent_samples, fault_tolerant_mode, n_batch_retries, wait_time_between_retries, expected_outputs, **config)
    results = []
    for batch in data:
        batch = launcher.predict(batch)
        assert batch[0]["error"] == "Test exception"
        results.append(batch)
    print(batch)