import os

default_home = os.path.join(os.path.expanduser("~"), ".cache")
flows_cache_home = os.path.expanduser(os.path.join(default_home, "flows"))
DEFAULT_CACHE_PATH = os.path.join(flows_cache_home, "flow_verse")

import sys
import importlib
from huggingface_hub import snapshot_download


def add_to_sys_path(path):
    # Make sure the path is absolute
    absolute_path = os.path.abspath(path)

    # Check if the path is in sys.path
    if absolute_path not in sys.path:
        # If it's not, add it
        sys.path.append(absolute_path)


def load_flow(repository_id, name, cache_dir=DEFAULT_CACHE_PATH):
    local_repo_path = snapshot_download(repo_id=repository_id, cache_dir=cache_dir)
    print("The flow was synced to:", local_repo_path)

    # split local_repo_path into parent and folder name
    local_repo_path_parent, local_repo_dir_name = os.path.dirname(local_repo_path), os.path.basename(local_repo_path)

    add_to_sys_path(local_repo_path_parent)
    _ = importlib.import_module(local_repo_dir_name)
    flow_module = importlib.import_module(f"{local_repo_dir_name}.{name}")
    flow_class = getattr(flow_module, name)
    return flow_class
