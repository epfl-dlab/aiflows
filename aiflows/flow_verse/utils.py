import os
import re


def build_hf_cache_path(repo_id: str, commit_hash: str, cache_root: str) -> str:
    """
    Builds the path to the cache directory for a given Hugging Face model.
    The path is constructed as follows:
    {CACHE_ROOT}/models--{username}--{modelname}/snapshots/{commit_hash}

    :param repo_id: The repository ID in the format of "username/modelname".
    :type repo_id: str
    :param commit_hash: The commit hash of the model snapshot.
    :type commit_hash: str
    :param cache_root: The root directory of the cache.
    :type cache_root: str
    :return: The path to the cache directory for the given model snapshot.
    :rtype: str
    """
    username, modelname = repo_id.split("/")
    relative_path = os.path.join(f"models--{username}--{modelname}", "snapshots", commit_hash)
    return os.path.join(cache_root, relative_path)


def is_local_revision(revision: str):
    """Returns True if the revision is a local revision, False otherwise.

    :param revision: The revision to check
    :type revision: str
    :return: True if the revision is a local revision, False otherwise
    :rtype: bool
    """
    return os.path.exists(revision)
