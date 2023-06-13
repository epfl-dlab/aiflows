import pytest
from flows.flow_launcher import BaseLauncher, MultiThreadedAPILauncher
from torch.utils.data import DataLoader, Dataset
from typing import List, Dict
from collections import defaultdict

class MockMultithreadedLauncher(MultiThreadedAPILauncher):

    def __init__(self, will_raise=False, will_alternate_success=False, **kwargs):
        super().__init__(**kwargs)
        self.batch_output = defaultdict(list)
        self.success = True
        self.will_raise = will_raise
        self.will_alternate_success = will_alternate_success
    def predict(self, batch: List[Dict], output_file: str = None) -> List[Dict]:
        inp = batch[0]
        inp["success"] = self.success
        if self.will_alternate_success:
            self.success = not self.success
        if self.will_raise:
            raise Exception("Test exception")
        batch = [inp]
        self.batch_output["default"].append(batch)
        return batch


    def write_batch_output(self, batch: List[Dict], output_file: str) -> None:
        self.batch_output[output_file] = batch

class MockDataset:
    def __init__(self, num_samples=2):
        # each dictionary is a batch
        data = [[{"id":idx, "query":f"query {idx}"}] for idx in range(num_samples)]
        self.data = data

def test_base_launcher():
    with pytest.raises(NotImplementedError):
        BaseLauncher().predict([])

    with pytest.raises(NotImplementedError):
        BaseLauncher().predict_dataloader(None, "test")

def test_get_outputs_to_write():
    batch = [
        {"id": 0, "inference_outputs": "test 0"},
        {"id": 1, "inference_outputs": "test 1", "success": False}
    ]
    keys_to_write = ["id", "inference_outputs"]

    expected_results = [{"id": 0, "inference_outputs": "test 0"},{"id": 1, "inference_outputs": "test 1"}]

    assert BaseLauncher._get_outputs_to_write(batch, keys_to_write) == expected_results
    assert BaseLauncher._get_outputs_to_write(batch, None) == expected_results

    # ToDo: logic for CF runs, to be removed
    keys_to_write = ["id", "inference_outputs", "success", "error"]
    expected_results= [{
        "id": 0, "inference_outputs": "test 0", "success": True, "error": "None"
    },{
        "id": 1, "inference_outputs": "test 1", "success": False, "error": "None"
    }]
    assert BaseLauncher._get_outputs_to_write(batch, keys_to_write) == expected_results

def test_init_multithreaded_launcher():
    config={
        "api_keys":["key1", "key2"],
    }
    launcher = MultiThreadedAPILauncher(**config)

    config={
        "api_keys":["key1", "key2"],
        "single_threaded":True
    }
    launcher = MultiThreadedAPILauncher(**config)

    config={
        "api_keys":["key1", "key2"],
        "n_workers_per_key":2,
    }
    launcher = MultiThreadedAPILauncher(**config)

def test_predict_dataloader(monkeypatch):

    num_samples = 10
    dataset = MockDataset(num_samples=num_samples)
    # ToDo: unclear whether we want to support batchsizes > 1
    dataloader = DataLoader(dataset, batch_size=1)

    config={
        "api_keys":["key1", "key2"],
        "debug":True
    }
    launcher = MockMultithreadedLauncher(**config)
    launcher.predict_dataloader(dataset.data, None)

    assert len(launcher.batch_output["default"]) == num_samples

    results = launcher.predict_dataloader(dataset.data, [{"id": 0, "inference_outputs": "test 0", "success": True, "error": "None"}])

    # there's one existing sample, it'll be written to the existing predictions key
    # the other newly generated output is appended to the default key
    assert len(launcher.batch_output['predictions/predictions_existing.jsonl']) == 1
    assert len(launcher.batch_output['default']) == 19
    config={
        "api_keys":["key1", "key2"],
        "debug":False
    }
    launcher = MockMultithreadedLauncher(**config)
    results = launcher.predict_dataloader(dataset.data, None)
    assert len(launcher.batch_output["default"]) == 10
    results = launcher.predict_dataloader(dataset.data, [{"id": 0, "inference_outputs": "test 0", "success": True, "error": "None"}])
    # there's one existing sample, it'll be written to the existing predictions key
    # the other newly generated output is appended to the default key
    assert len(launcher.batch_output['predictions/predictions_existing.jsonl']) == 1
    assert len(launcher.batch_output['default']) == 19

    # the launcher exits with an error code if an exception is raised
    with pytest.raises(SystemExit):
        exploding_launcher = MockMultithreadedLauncher(will_raise=True, **config)
        exploding_launcher.predict_dataloader(dataset.data, None)

    # the launcher counts the number of errors
    launcher = MockMultithreadedLauncher(will_alternate_success=True, **config)
    results = launcher.predict_dataloader(dataset.data, None)

    print(results)