import pytest
from flows.flow_launcher import BaseLauncher

def test_base_launcher():
    with pytest.raises(NotImplementedError):
        BaseLauncher().predict([], "test")

    with pytest.raises(NotImplementedError):
        BaseLauncher().predict_dataloader(None, "test")

def test_get_outputs_to_write():
    batch = [
        {"id": 0, "inference_outputs": "test 0"},
        {"id": 1, "inference_outputs": "test 1", "success": False}
    ]
    keys_to_write = ["id", "inference_outputs"]

    expected_results = [{
        "id": 0, "inference_outputs": "test 0"
    },{"id": 1, "inference_outputs": "test 1"}]

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