import os

def build_hf_cache_path(username: str, modelname: str, commit_hash: str, cache_root: str) -> str:
    """
    Builds the path to the cache directory for a given Hugging Face model.
    {CACHE_ROOT}/models--{username}--{modelname}/snapshots/{commit_hash}

    :param username: The username of the model owner.
    :type username: str
    :param modelname: The name of the model.
    :type modelname: str
    :param commit_hash: The commit hash of the model snapshot.
    :type commit_hash: str
    :param cache_root: The root directory of the cache.
    :type cache_root: str
    :return: The path to the cache directory for the given model snapshot.
    :rtype: str
    """
    relative_path = os.path.join(
        f"models--{username}--{modelname}",
        "snapshots",
        commit_hash
    )
    return os.path.join(cache_root, relative_path)
