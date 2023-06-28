import os
import pdb

default_home = os.path.join(os.path.expanduser("~"), ".cache")
flows_cache_home = os.path.expanduser(os.path.join(default_home, "flows"))
DEFAULT_CACHE_PATH = os.path.join(flows_cache_home, "flow_verse")

import sys
import importlib
import huggingface_hub


def add_to_sys_path(path):
    # Make sure the path is absolute
    absolute_path = os.path.abspath(path)

    # Check if the path is in sys.path
    if absolute_path not in sys.path:
        # If it's not, add it
        sys.path.append(absolute_path)


def _is_local_path(path_to_dir):
    """Returns True if path_to_dir is a path to a local directory."""

    # check if the directory exists
    if os.path.isdir(path_to_dir):
        # check if directory is not empty
        if os.listdir(path_to_dir):
            return True
        else:
            return False
    else:
        return False


def _sync_repository(repository_id, cache_dir=DEFAULT_CACHE_PATH, local_dir=None, override=False, **kwargs):
    if override:
        path_to_local_repository = huggingface_hub.snapshot_download(repository_id, cache_dir=cache_dir, local_dir=local_dir,  **kwargs)
    elif _is_local_path(repository_id):
        path_to_local_repository = repository_id
    else:
        path_to_local_repository = huggingface_hub.snapshot_download(repository_id, cache_dir=cache_dir, local_dir=local_dir,  **kwargs)

    print("The flow repository was synced to:", path_to_local_repository)  # ToDo: Replace with log.info once the logger is set up
    return path_to_local_repository


def load_config(repository_id, class_name, cache_dir=DEFAULT_CACHE_PATH, local_dir=None, overrides={}):
    flow_class = load_class(repository_id=repository_id,
                            class_name=class_name,
                            local_dir=local_dir,
                            cache_dir=cache_dir)

    config = flow_class.get_config(**overrides)

    return config


def load_class(repository_id, class_name, cache_dir=DEFAULT_CACHE_PATH, local_dir=None):
    path_to_local_repository = _sync_repository(repository_id,
                                                local_dir=local_dir,
                                                cache_dir=cache_dir)

    # split local_repo_path into parent and folder name
    local_repo_path_parent = os.path.dirname(path_to_local_repository)
    local_repo_dir_name = os.path.basename(path_to_local_repository)

    add_to_sys_path(local_repo_path_parent)
    flow_module = importlib.import_module(local_repo_dir_name)
    flow_class = getattr(flow_module, class_name)

    return flow_class


def instantiate_flow(repository_id, class_name, cache_dir=DEFAULT_CACHE_PATH, local_dir=None, overrides={}):
    flow_class = load_class(repository_id=repository_id,
                            local_dir=local_dir,
                            class_name=class_name,
                            cache_dir=cache_dir)

    config = flow_class.get_config(**overrides)

    return flow_class.instantiate_from_config(config)


