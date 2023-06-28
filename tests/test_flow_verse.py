from flows.flow_verse import loading
from flows.base_flows import Flow
import sys
import os
import tempfile
import huggingface_hub


def test_add_to_sys_path(monkeypatch):
    mocked_sys_path = []
    monkeypatch.setattr(sys, "path", mocked_sys_path)

    new_path = "test_path"

    assert len(sys.path) == 0
    loading.add_to_sys_path(new_path)
    assert len(sys.path) == 1

    assert os.path.split(sys.path[0])[-1] == new_path


def test_is_local_path_patched(monkeypatch):
    # check behaviour for directory
    monkeypatch.setattr(os.path, "isdir", lambda x: True)
    monkeypatch.setattr(os, "listdir", lambda x: ["file1", "file2"])
    assert loading._is_local_path("test_path") == True
    monkeypatch.setattr(os, "listdir", lambda x: [])
    assert loading._is_local_path("test_path") == False

    # check behaviour for file
    monkeypatch.setattr(os.path, "isdir", lambda x: False)
    assert loading._is_local_path("test_path") == False


def test_is_local_path():
    with tempfile.TemporaryDirectory(dir="./") as temp_dir:
        assert loading._is_local_path(temp_dir) == False
        with open(os.path.join(temp_dir, "test.txt"), "w") as f:
            f.write("unit test")
        assert loading._is_local_path(temp_dir) == True


def test_sync_repository_to_working_dir():
    pass


def test_sync_repository(monkeypatch):
    with tempfile.TemporaryDirectory(dir="./") as temp_dir:
        loading._sync_repository("lhk/test_model", local_dir=temp_dir)
        with open(os.path.join(temp_dir, "test.txt"), "r") as f:
            assert f.read() == "unit test"


def test_load_config(monkeypatch):
    config = """
# This is an abstract flow, therefore some required fields are missing (not defined)

n_api_retries: 5
wait_time_between_retries: 20

system_name: system
user_name: user
assistant_name: assistant

response_annotators: {}

query_message_prompt_template: null  # ToDo: When will this be null?
demonstrations: null
demonstrations_response_template: null
"""
    with tempfile.TemporaryDirectory(dir="./") as temp_dir:
        # manually writing the config file, loading as local path
        with open(os.path.join(temp_dir, "config.yaml"), "w") as f:
            f.write(config)

        config = loading.load_config(temp_dir, "config")
        assert config is not None
        assert config["n_api_retries"] == 5

    with tempfile.TemporaryDirectory(dir="./") as temp_dir:
        # triggering syncdir
        config = loading.load_config("lhk/test_model", "config", local_dir=temp_dir)
        assert config is not None
        assert config["n_api_retries"] == 6


def test_syncdir_override(monkeypatch):
    monkeypatch.setattr(huggingface_hub, "snapshot_download", lambda x, **kwargs: x)
    config = """
n_api_retries: -1
"""
    with tempfile.TemporaryDirectory(dir="./") as temp_dir:
        # manually writing the config file, loading as local path
        with open(os.path.join(temp_dir, "config.yaml"), "w") as f:
            f.write(config)

        config = loading.load_config(temp_dir, "config", override=True)
        assert config is not None
        assert config["n_api_retries"] == -1


def test_load_class(monkeypatch):
    loaded_class = loading.load_class("lhk/test_model", "MockedFlow")
    assert loaded_class is not None


def test_instantiate(monkeypatch):
    flow = loading.instantiate_flow("lhk/test_model", "MockedFlow")
    assert flow.flow_type == "mocked"


def test_get_config_from_abstract(monkeypatch):
    class MockedVerseFlow(Flow):
        repository_id = "lhk/test_model"
        class_name = "MockedFlow"

    MockedVerseFlow.get_config()
