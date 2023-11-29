import os
import sys
import mock
import pytest
import importlib
import functools
from typing import Tuple

import flows
from flows.flow_verse.loading import (
    _sync_dependencies,
    FlowModuleSpecSummary,
    FlowModuleSpec,
    DEFAULT_FLOW_MODULE_FOLDER,
    NO_COMMIT_HASH,
    is_sync_dir_modified,
    add_to_sys_path,
)
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
    ret = os.path.join(tmpdir, DEFAULT_FLOW_MODULE_FOLDER)
    return ret


@pytest.fixture(autouse=True)
def restore_sys_path_after_test():
    original = sys.path[:]
    yield None
    sys.path = original[:]


@pytest.fixture(autouse=True)
def mock_sync_flow_dependencies(tmpdir, cache_root):
    with mock.patch(
        "flows.flow_verse.sync_dependencies",
        new=functools.partial(
            _sync_dependencies,
            flow_modules_base_dir=tmpdir,
            cache_root=cache_root,
            caller_module_name="<test>",
            all_overwrite=False,
        ),
    ) as mock_sync:
        yield mock_sync
    # flows.flow_verse.sync_dependencies = functools.partial(_sync_dependencies, flow_modules_base_dir=tmpdir, cache_root=cache_root, caller_module_name="<test>")


@pytest.fixture
def local_sync_1f_UsefulChatBots(tmpdir, cache_root, sync_root, local_dev_path):
    dependencies = [
        {"url": "1f/UsefulChatBots", "revision": local_dev_path},
    ]
    flow_mod_summary = _sync_dependencies(dependencies, False, tmpdir, cache_root, "<test>")

    correct_summary = FlowModuleSpecSummary(
        sync_root,
        cache_root,
        mods=[
            FlowModuleSpec(
                "1f/UsefulChatBots",
                local_dev_path,
                NO_COMMIT_HASH,
                local_dev_path,
                os.path.join(sync_root, "user_1f/UsefulChatBots"),
            )
        ],
    )
    return flow_mod_summary, correct_summary


@pytest.fixture
def remote_sync_yeeef_UsefulChatBots(tmpdir, cache_root, sync_root):
    dependencies = [
        {"url": "yeeef/UsefulChatBots", "revision": "main"},
    ]
    flow_mod_summary = _sync_dependencies(dependencies, False, tmpdir, cache_root, "<test>")

    correct_summary = FlowModuleSpecSummary(
        sync_root,
        cache_root,
        mods=[
            FlowModuleSpec(
                "yeeef/UsefulChatBots",
                "main",
                "7f69d13b46d20e02fa3883b3059e6e4f656af20f",
                build_hf_cache_path("yeeef/UsefulChatBots", "7f69d13b46d20e02fa3883b3059e6e4f656af20f", cache_root),
                os.path.join(sync_root, "yeeef/UsefulChatBots/"),
            )
        ],
    )
    return flow_mod_summary, correct_summary


@pytest.fixture
def local_dev_path(tmpdir, cache_root, sync_root):
    dev_path = os.path.join(tmpdir, "dev/yeeef/dev_LocalUsefulChatBots")
    os.makedirs(dev_path)
    return dev_path


@pytest.fixture
def local_sync_yeeef_LocalUsefulChatBots(tmpdir, cache_root, sync_root, local_dev_path: str):
    dependencies = [
        {"url": "yeeef/LocalUsefulChatBots", "revision": local_dev_path},
    ]
    flow_mod_summary = _sync_dependencies(dependencies, False, tmpdir, cache_root, "<test>")

    correct_summary = FlowModuleSpecSummary(
        sync_root,
        cache_root,
        mods=[
            FlowModuleSpec(
                "yeeef/LocalUsefulChatBots",
                local_dev_path,
                NO_COMMIT_HASH,
                local_dev_path,
                os.path.join(sync_root, "yeeef/LocalUsefulChatBots"),
            )
        ],
    )
    return flow_mod_summary, correct_summary


@pytest.fixture
def local_sync_yeeef_UsefulChatBots(tmpdir, cache_root, sync_root, local_dev_path: str):
    dependencies = [
        {"url": "yeeef/UsefulChatBots", "revision": local_dev_path},
    ]
    flow_mod_summary = _sync_dependencies(dependencies, False, tmpdir, cache_root, "<test>")

    correct_summary = FlowModuleSpecSummary(
        sync_root,
        cache_root,
        mods=[
            FlowModuleSpec(
                "yeeef/UsefulChatBots",
                local_dev_path,
                NO_COMMIT_HASH,
                local_dev_path,
                os.path.join(sync_root, "yeeef/UsefulChatBots"),
            )
        ],
    )
    return flow_mod_summary, correct_summary


def test_single_remote(remote_sync_yeeef_UsefulChatBots: Tuple[FlowModuleSpecSummary, FlowModuleSpecSummary]):
    flow_mod_summary, correct_summary = remote_sync_yeeef_UsefulChatBots
    assert_flow_module_summary(flow_mod_summary, correct_summary)


def test_single_local(local_sync_yeeef_LocalUsefulChatBots: Tuple[FlowModuleSpecSummary, FlowModuleSpecSummary]):
    flow_mod_summary, correct_summary = local_sync_yeeef_LocalUsefulChatBots
    assert_flow_module_summary(flow_mod_summary, correct_summary)


def test_single_remote_overwrite(
    tmpdir, cache_root, sync_root, remote_sync_yeeef_UsefulChatBots: Tuple[FlowModuleSpecSummary, FlowModuleSpecSummary]
):
    flow_mod_summary, correct_summary = remote_sync_yeeef_UsefulChatBots
    assert_flow_module_summary(flow_mod_summary, correct_summary)

    to_modify_mod = flow_mod_summary.get_mods()[0]
    original_content = ""
    written_content = "modified\n"
    with open(os.path.join(to_modify_mod.sync_dir, "README.md"), "r") as f:
        original_content = f.read()

    # user accept overwrite
    with open(os.path.join(to_modify_mod.sync_dir, "README.md"), "w") as f:
        f.write(written_content)
    assert is_sync_dir_modified(to_modify_mod.sync_dir, to_modify_mod.cache_dir)

    dependencies = [
        {"url": "yeeef/UsefulChatBots", "revision": "main", "overwrite": True},
    ]
    with mock.patch("builtins.input", return_value="Y"):
        flow_mod_summary = _sync_dependencies(dependencies, False, tmpdir, cache_root, "<test>")

    assert_flow_module_summary(flow_mod_summary, correct_summary)
    with open(os.path.join(to_modify_mod.sync_dir, "README.md"), "r") as f:
        assert f.read() == original_content

    # user reject overwrite
    with open(os.path.join(to_modify_mod.sync_dir, "README.md"), "w") as f:
        f.write(written_content)
    assert is_sync_dir_modified(to_modify_mod.sync_dir, to_modify_mod.cache_dir)
    dependencies = [
        {"url": "yeeef/UsefulChatBots", "revision": "main", "overwrite": True},
    ]
    with mock.patch("builtins.input", return_value="n"):
        flow_mod_summary = _sync_dependencies(dependencies, False, tmpdir, cache_root, "<test>")

    assert_flow_module_summary(flow_mod_summary, correct_summary)
    with open(os.path.join(to_modify_mod.sync_dir, "README.md"), "r") as f:
        assert f.read() == written_content


def test_remote_revision_to_local(
    tmpdir,
    cache_root,
    sync_root,
    remote_sync_yeeef_UsefulChatBots: Tuple[FlowModuleSpecSummary, FlowModuleSpecSummary],
    local_dev_path: str,
):
    _, original_correct_summary = remote_sync_yeeef_UsefulChatBots
    assert_flow_module_summary(*remote_sync_yeeef_UsefulChatBots)

    dependencies = [
        {"url": "yeeef/UsefulChatBots", "revision": local_dev_path},
    ]

    with mock.patch("builtins.input", return_value="y"):  # y is not Y!
        flow_mod_summary = _sync_dependencies(dependencies, False, tmpdir, cache_root, "<test>")

    assert_flow_module_summary(flow_mod_summary, original_correct_summary)

    with mock.patch("builtins.input", return_value="Y"):
        flow_mod_summary = _sync_dependencies(dependencies, False, tmpdir, cache_root, "<test>")

    correct_summary = FlowModuleSpecSummary(
        sync_root,
        cache_root,
        mods=[
            FlowModuleSpec(
                "yeeef/UsefulChatBots",
                local_dev_path,
                NO_COMMIT_HASH,
                local_dev_path,
                os.path.join(sync_root, "yeeef/UsefulChatBots"),
            )
        ],
    )

    assert_flow_module_summary(flow_mod_summary, correct_summary)


def test_local_revision_to_remote(
    tmpdir, cache_root, sync_root, local_sync_yeeef_UsefulChatBots: Tuple[FlowModuleSpecSummary, FlowModuleSpecSummary]
):
    _, orignal_correct_summary = local_sync_yeeef_UsefulChatBots
    assert_flow_module_summary(*local_sync_yeeef_UsefulChatBots)

    dependencies = [
        {"url": "yeeef/UsefulChatBots", "revision": "main"},
    ]

    with mock.patch("builtins.input", return_value="asdfsadf"):
        flow_mod_summary = _sync_dependencies(dependencies, False, tmpdir, cache_root, "<test>")

    assert_flow_module_summary(flow_mod_summary, orignal_correct_summary)

    with mock.patch("builtins.input", return_value="Y"):
        flow_mod_summary = _sync_dependencies(dependencies, False, tmpdir, cache_root, "<test>")

    correct_summary = FlowModuleSpecSummary(
        sync_root,
        cache_root,
        mods=[
            FlowModuleSpec(
                "yeeef/UsefulChatBots",
                "main",
                "7f69d13b46d20e02fa3883b3059e6e4f656af20f",
                build_hf_cache_path("yeeef/UsefulChatBots", "7f69d13b46d20e02fa3883b3059e6e4f656af20f", cache_root),
                os.path.join(sync_root, "yeeef/UsefulChatBots"),
            )
        ],
    )
    assert_flow_module_summary(flow_mod_summary, correct_summary)


def test_bizzar_username(local_sync_1f_UsefulChatBots):
    assert_flow_module_summary(*local_sync_1f_UsefulChatBots)


def test_sync_dependency_chain(
    tmpdir, cache_root, sync_root, remote_sync_yeeef_UsefulChatBots: Tuple[FlowModuleSpecSummary, FlowModuleSpecSummary]
):
    flow_mod_summary, _ = remote_sync_yeeef_UsefulChatBots
    assert_flow_module_summary(*remote_sync_yeeef_UsefulChatBots)
    assert len(flow_mod_summary.get_mods()) == 1, flow_mod_summary.get_mods()

    sync_dir = os.path.relpath(flow_mod_summary.get_mods()[0].sync_dir, tmpdir)
    importlib.import_module(sync_dir.replace("/", "."))
    # import flow_modules.yeeef.UsefulChatBots

    new_flow_mod_summary = FlowModuleSpecSummary.from_flow_mod_file(os.path.join(sync_root, "flow.mod"))
    correct_summary = FlowModuleSpecSummary(
        sync_root,
        cache_root,
        mods=[
            FlowModuleSpec(
                "yeeef/UsefulChatBots",
                "main",
                "7f69d13b46d20e02fa3883b3059e6e4f656af20f",
                build_hf_cache_path("yeeef/UsefulChatBots", "7f69d13b46d20e02fa3883b3059e6e4f656af20f", cache_root),
                os.path.join(sync_root, "yeeef/UsefulChatBots/"),
            ),
            FlowModuleSpec(
                "yeeef/GPT4Flow",
                "main",
                "4b2766dd0229d2e9b6f6887b163522f03aefd83f",
                build_hf_cache_path("yeeef/GPT4Flow", "4b2766dd0229d2e9b6f6887b163522f03aefd83f", cache_root),
                os.path.join(sync_root, "yeeef/GPT4Flow/"),
            ),
        ],
    )
    assert_flow_module_summary(new_flow_mod_summary, correct_summary)


# TODO(yeeef)
# def test_remote_revision_change_commit_hash

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
            FlowModuleSpec(
                "yeeef/UsefulChatBots",
                "main",
                "7f69d13b46d20e02fa3883b3059e6e4f656af20f",
                build_hf_cache_path("yeeef/UsefulChatBots", "7f69d13b46d20e02fa3883b3059e6e4f656af20f", cache_root),
                os.path.join(sync_root, "yeeef/UsefulChatBots/"),
            )
        ],
    )
    assert flow_mod_summary.serialize() == correct_summary.serialize()
