import os
import re
import colorama

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
    breakpoint()
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

def yes_no_question(logger,question_message,yes_message, no_message, colorama_style=colorama.Fore.RED):
    """Asks a yes/no question and returns True if the user answers yes, False otherwise.
    
    :param question_message: The message to display when asking the question
    :type question_message: str
    :param yes_message: The message to display when the user answers yes
    :type yes_message: str
    :param no_message: The message to display when the user answers no
    :type no_message: str
    :param colarama_style: The colorama style to use when displaying the question, defaults to colorama.Fore.RED
    :type colarama_style: colorama.Fore, optional
    :return: True if the user answers yes, False otherwise
    :rtype: bool
    """
    while True:
        
        logger.warn(
                f""" {colorama_style} {question_message} (Y/N){colorama.Style.RESET_ALL}"""
        )
        user_input = input()
        
        if user_input == "Y":
            logger.warn(
                f"{colorama_style}  {yes_message} {colorama.Style.RESET_ALL}"
            )
            break
        
        elif user_input == "N":
            logger.warn(
                f"{colorama_style}  {no_message} {colorama.Style.RESET_ALL}"
            )
            break
        
        else:
            logger.warn("Invalid input. Please enter 'Y' or 'N'.")
            
    
    return user_input == "Y"
