import os
import mock
import pytest
from typing import Tuple

from flows.flow_verse.loading import _sync_dependencies, FlowModuleSpecSummary, FlowModuleSpec, DEFAULT_FLOW_MODULE_FOLDER, NO_COMMIT_HASH, is_sync_dir_modified
from flows.flow_verse.utils import build_hf_cache_path

########## positive tests

def assert_flow_module_summary(flow_mod_summary: FlowModuleSpecSummary, correct_summary: FlowModuleSpecSummary):
    assert flow_mod_summary.serialize() == correct_summary.serialize()

    # check cache dir and sync dir are correctly generated
    for mod in flow_mod_summary.get_mods():
        assert os.path.isdir(mod.sync_dir)
        assert os.path.isdir(mod.cache_dir)


@pytest.fixture
def cache_root(tmpdir: str):
    return os.path.join(tmpdir, "flow_verse")

@pytest.fixture
def sync_root(tmpdir: str):
    return os.path.join(tmpdir, DEFAULT_FLOW_MODULE_FOLDER)


@pytest.fixture
def sync_yeeef_UsefulChatBots(tmpdir, cache_root, sync_root):
    dependencies = [
        {"url": "yeeef/UsefulChatBots", "revision": "main"},
    ]
    flow_mod_summary = _sync_dependencies(dependencies, False, tmpdir, cache_root, "<test>") 

    correct_summary = FlowModuleSpecSummary(
        sync_root,
        cache_root,
        mods=[
            FlowModuleSpec("yeeef/UsefulChatBots", 
                           "main", 
                           "7f69d13b46d20e02fa3883b3059e6e4f656af20f", 
                           build_hf_cache_path("yeeef/UsefulChatBots", "7f69d13b46d20e02fa3883b3059e6e4f656af20f", cache_root),
                           os.path.join(sync_root, "yeeef/UsefulChatBots/")
            )
        ]
    )
    return flow_mod_summary, correct_summary

@pytest.fixture
def local_dev_path(tmpdir, cache_root, sync_root):
    dev_path = os.path.join(tmpdir, "dev/yeeef/dev_LocalUsefulChatBots")
    os.makedirs(dev_path)
    return dev_path

@pytest.fixture
def sync_yeeef_LocalUsefulChatBots(tmpdir, cache_root, sync_root, local_dev_path: str):
    dependencies = [
        {"url": "yeeef/LocalUsefulChatBots", "revision": local_dev_path},
    ]
    flow_mod_summary = _sync_dependencies(dependencies, False, tmpdir, cache_root, "<test>") 

    correct_summary = FlowModuleSpecSummary(
        sync_root,
        cache_root,
        mods=[
            FlowModuleSpec("yeeef/LocalUsefulChatBots", 
                           local_dev_path, 
                           NO_COMMIT_HASH, 
                           local_dev_path,
                           os.path.join(sync_root, "yeeef/LocalUsefulChatBots")
            )
        ]
    )
    return flow_mod_summary, correct_summary

def test_single_remote(sync_yeeef_UsefulChatBots: Tuple[FlowModuleSpecSummary, FlowModuleSpecSummary]):
    flow_mod_summary, correct_summary = sync_yeeef_UsefulChatBots
    assert_flow_module_summary(flow_mod_summary, correct_summary)

def test_single_local(sync_yeeef_LocalUsefulChatBots: Tuple[FlowModuleSpecSummary, FlowModuleSpecSummary]):
    flow_mod_summary, correct_summary = sync_yeeef_LocalUsefulChatBots
    assert_flow_module_summary(flow_mod_summary, correct_summary)

def test_single_remote_overwrite(tmpdir, cache_root, sync_root, sync_yeeef_UsefulChatBots: Tuple[FlowModuleSpecSummary, FlowModuleSpecSummary]):
    flow_mod_summary, correct_summary = sync_yeeef_UsefulChatBots
    assert_flow_module_summary(flow_mod_summary, correct_summary)

    # modify the file in sync dir
    to_modify_mod = flow_mod_summary.get_mods()[0]
    with open(os.path.join(to_modify_mod.sync_dir, "README.md"), "w") as f:
        f.write("modified\n")

    assert is_sync_dir_modified(to_modify_mod.sync_dir, to_modify_mod.cache_dir)

    dependencies = [
        {"url": "yeeef/UsefulChatBots", "revision": "main", "overwrite": True},
    ]
    with mock.patch.object(__builtins__, 'input', lambda: "Y"):
        flow_mod_summary = _sync_dependencies(dependencies, False, tmpdir, cache_root, "<test>") 

    assert_flow_module_summary(flow_mod_summary, correct_summary)
    with open(os.path.join(to_modify_mod.sync_dir, "README.md"), "r") as f:
        assert f.read() == ""

################ negative tests

def test_single_remote_not_exist(tmpdir: str):
    dependencies = [
        {"url": "yeeef/LocalUsefulChatBots", "revision": "main"},
    ]
    cache_root = os.path.join(tmpdir, "flow_verse")
    try:
        _ = _sync_dependencies(dependencies, False, tmpdir, cache_root, "<test>") 
    except:
        return

    assert False, "it should raise exception, because yeeef/LocalUsefulChatBots does not exist remotely"

def test_single_local_not_exist(tmpdir: str):
    dev_path = os.path.join(tmpdir, "dev/yeeef/dev_LocalUsefulChatBots")

    dependencies = [
        {"url": "yeeef/LocalUsefulChatBots", "revision": dev_path},
    ]
    cache_root = os.path.join(tmpdir, "flow_verse")
    try:
        _ = _sync_dependencies(dependencies, False, tmpdir, cache_root, "<test>") 
    except:
        return

    assert False, "it should raise exception, because yeeef/LocalUsefulChatBots does not exist remotely"

    dependencies = [
        {"url": "yeeef/UsefulChatBots", "revision": "main"},
    ]
    cache_root = os.path.join(tmpdir, "flow_verse")
    sync_root = os.path.join(tmpdir, DEFAULT_FLOW_MODULE_FOLDER)
    flow_mod_summary = _sync_dependencies(dependencies, False, tmpdir, cache_root, "<test>") 
    flow_mod_summary = _sync_dependencies(dependencies, True, tmpdir, cache_root, "<test>") 

    correct_summary = FlowModuleSpecSummary(
        sync_root,
        cache_root,
        mods=[
            FlowModuleSpec("yeeef/UsefulChatBots", 
                           "main", 
                           "7f69d13b46d20e02fa3883b3059e6e4f656af20f", 
                           build_hf_cache_path("yeeef/UsefulChatBots", "7f69d13b46d20e02fa3883b3059e6e4f656af20f", cache_root),
                           os.path.join(sync_root, "yeeef/UsefulChatBots/")
            )
        ]
    )
    assert flow_mod_summary.serialize() == correct_summary.serialize()