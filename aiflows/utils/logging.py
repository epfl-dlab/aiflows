# coding=utf-8
# Copyright 2020 Optuna, Hugging Face
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
""" Logging utilities."""
import errno
import functools
import inspect
import logging
import os
import shutil
import sys
import threading
from datetime import datetime
from logging import (
    CRITICAL,  # NOQA
    DEBUG,  # NOQA
    ERROR,  # NOQA
    FATAL,  # NOQA
    INFO,  # NOQA
    NOTSET,  # NOQA
    WARN,  # NOQA
    WARNING,  # NOQA
)
from typing import Optional

_lock = threading.Lock()
_default_handler: Optional[logging.Handler] = None
_logger = None

log_levels = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL,
}

_default_log_level = log_levels["info"]
LOG_DIR = None
_FILE_HANDLER = None

import logging.config

from omegaconf import OmegaConf


def _init_logger_from_cfg():
    """Initialize the logger from the config file"""
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    logger_cfg_path = os.path.join(root_dir, "configs/python_logger.yaml")
    with open(logger_cfg_path, "r") as f:
        logger_cfg = OmegaConf.load(f)

    conf = OmegaConf.to_container(logger_cfg, resolve=True)
    logging.config.dictConfig(conf)


def _get_default_logging_level():
    """
    If FLOWS_VERBOSITY env var is set to one of the valid choices return that as the new default level. If it is
    not - fall back to `_default_log_level`
    """
    env_level_str = os.getenv("FLOWS_VERBOSITY", None)
    if env_level_str:
        if env_level_str in log_levels:
            return log_levels[env_level_str]
        else:
            logging.getLogger().warning(
                f"Unknown option FLOWS_VERBOSITY={env_level_str}, " f"has to be one of: {', '.join(log_levels.keys())}"
            )
    return _default_log_level


def _get_library_name() -> str:
    """Return the name of the library."""
    return __name__.split(".")[0]


def _get_library_root_logger() -> logging.Logger:
    """Return the root logger of the library."""
    return logging.getLogger(_get_library_name())


def _configure_library_root_logger() -> None:
    """Configure the root logger of the library."""
    global _default_handler
    global _logger

    with _lock:
        if _default_handler:
            # This library has already configured the library root logger.
            return
        _init_logger_from_cfg()
        _logger = _get_library_root_logger()
        _logger.setLevel(_get_default_logging_level())
        _default_handler = _logger.handlers[0]


_configure_library_root_logger()


def _reset_library_root_logger() -> None:
    """Reset the root logger of the library."""
    global _default_handler

    with _lock:
        if not _default_handler:
            return

        library_root_logger = _get_library_root_logger()
        library_root_logger.removeHandler(_default_handler)
        library_root_logger.setLevel(logging.NOTSET)
        _default_handler = None


def get_log_levels_dict():
    """Return a dictionary of all available log levels."""
    return log_levels


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Return a logger with the specified name.
    This function is not supposed to be directly accessed unless you are writing a custom aiflows module.

    :param name: The name of the logger to return
    :type name: str, optional
    :return: The logger
    """

    if name is None:
        name = _get_library_name()

    _configure_library_root_logger()
    return logging.getLogger(name)


def get_verbosity() -> int:
    """
    Return the current level for the Flows's root logger as an int.

    :return: The logging level
    :rtype: int

    .. note::
        Flows has following logging levels:

        - 50: `aiflows.logging.CRITICAL` or `aiflows.logging.FATAL`
        - 40: `aiflows.logging.ERROR`
        - 30: `aiflows.logging.WARNING` or `aiflows.logging.WARN`
        - 20: `aiflows.logging.INFO`
        - 10: `aiflows.logging.DEBUG`
    """
    _configure_library_root_logger()
    return _get_library_root_logger().getEffectiveLevel()


def set_verbosity(verbosity: int) -> None:
    """
    Set the verbosity level for the Flows's root logger.

    :param verbosity: Logging level. For example, it can be one of the following:
            - `aiflows.logging.CRITICAL` or `aiflows.logging.FATAL`
            - `aiflows.logging.ERROR`
            - `aiflows.logging.WARNING` or `aiflows.logging.WARN`
            - `aiflows.logging.INFO`
            - `aiflows.logging.DEBUG`
    :type verbosity: int
    """

    _configure_library_root_logger()
    _get_library_root_logger().setLevel(verbosity)


def set_verbosity_info():
    """Set the verbosity to the `INFO` level."""
    return set_verbosity(INFO)


def set_verbosity_warning():
    """Set the verbosity to the `WARNING` level."""
    return set_verbosity(WARNING)


def set_verbosity_debug():
    """Set the verbosity to the `DEBUG` level."""
    return set_verbosity(DEBUG)


def set_verbosity_error():
    """Set the verbosity to the `ERROR` level."""
    return set_verbosity(ERROR)


def disable_default_handler() -> None:
    """Disable the default handler of the Flows's root logger."""

    _configure_library_root_logger()

    assert _default_handler is not None
    _get_library_root_logger().removeHandler(_default_handler)


def enable_default_handler() -> None:
    """Enable the default handler of the Flows's root logger."""

    _configure_library_root_logger()

    assert _default_handler is not None
    _get_library_root_logger().addHandler(_default_handler)


def add_handler(handler: logging.Handler) -> None:
    """adds a handler to the Flows's root logger."""

    _configure_library_root_logger()

    assert handler is not None
    _get_library_root_logger().addHandler(handler)


def remove_handler(handler: logging.Handler) -> None:
    """removes given handler from the Flows's root logger."""

    _configure_library_root_logger()

    assert handler is not None and handler not in _get_library_root_logger().handlers
    _get_library_root_logger().removeHandler(handler)


def disable_propagation() -> None:
    """
    Disable propagation of the library log outputs. Note that log propagation is disabled by default.
    """

    _configure_library_root_logger()
    _get_library_root_logger().propagate = False


def enable_propagation() -> None:
    """
    Enable propagation of the library log outputs. Please disable the Flows's default handler to
    prevent double logging if the root logger has been configured.
    """

    _configure_library_root_logger()
    _get_library_root_logger().propagate = True


def enable_explicit_format() -> None:
    """
    Enable explicit formatting for every Flows's logger. The explicit formatter is as follows::

        [LEVELNAME|FILENAME|LINE NUMBER] TIME >> MESSAGE

    All handlers currently bound to the root logger are affected by this method.
    """

    handlers = _get_library_root_logger().handlers

    for handler in handlers:
        formatter = logging.Formatter("[%(levelname)s|%(filename)s:%(lineno)s] %(asctime)s >> %(message)s")
        handler.setFormatter(formatter)


def reset_format() -> None:
    """
    Resets the formatting for Flows's loggers.
    All handlers currently bound to the root logger are affected by this method.
    """
    handlers = _get_library_root_logger().handlers

    for handler in handlers:
        handler.setFormatter(None)


def warning_advice(self, *args, **kwargs):
    r"""
    This method is identical to `logger.warning()`, but if env var FLOWS_NO_ADVISORY_WARNINGS=1 is set, this
    warning will not be printed

    :param self: The logger object
    :param \*args: The arguments to pass to the warning method
    :param \**kwargs: The keyword arguments to pass to the warning method
    """
    no_advisory_warnings = os.getenv("FLOWS_NO_ADVISORY_WARNINGS", False)
    if no_advisory_warnings:
        return
    self.warning(*args, **kwargs)


logging.Logger.warning_advice = warning_advice


@functools.lru_cache(None)
def warning_once(self, *args, **kwargs):
    """
    This method is identical to `logger.warning()`, but will emit the warning with the same message only once

    .. note::
        The cache is for the function arguments, so 2 different callers using the same arguments will hit the cache.
        The assumption here is that all warning messages are unique across the code. If they aren't then need to switch to
        another type of cache that includes the caller frame information in the hashing function.
    """
    self.warning(*args, **kwargs)


logging.Logger.warning_once = warning_once


########################
#
# File logging
#
########################


def _get_time_str():
    """Return formatted time string (format: '%Y-%m-%d_%H-%M-%S')

    :return: The formatted time string
    :rtype: str
    """
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


def _set_file(path):
    """Add a file handler to the global logger.

    :param path: The path to the file
    :type path: str
    """
    global _FILE_HANDLER
    _logger = _get_library_root_logger()
    if os.path.isfile(path):
        backup_name = path + "." + _get_time_str()
        shutil.move(path, backup_name)
        _logger.info("Existing log file '{}' backuped to '{}'".format(path, backup_name))  # noqa: F821
    file_hdl = logging.FileHandler(filename=path, encoding="utf-8", mode="w")
    formatter = _logger.handlers[0].formatter

    file_hdl.setFormatter(formatter)

    _FILE_HANDLER = file_hdl
    _logger.addHandler(file_hdl)
    _logger.info("Argv: " + " ".join(sys.argv))


def set_dir(dirname, action=None):
    """
    Set the directory for global logging.
    :param dirname: log directory
    :type dirname: str
    :param action: an action of ["k","d","q"] to be performed when the directory exists.
    When the directory exists, Will ask user by default.
    - "d": delete the directory. Note that the deletion may fail when
    the directory is used by tensorboard.
    - "k": keep the directory. This is useful when you resume from a
    previous training and want the directory to look as if the
    training was not interrupted.
    Note that this option does not load old models or any other
    old states for you. It simply does nothing.
   
    :param dirname: log directory
    :type dirname: str
    :param action: an action of ["k","d","q"] to be performed when the directory exists.
        When the directory exists, Will ask user by default.
        - "d": delete the directory. Note that the deletion may fail when
        the directory is used by tensorboard.
        - "k": keep the directory. This is useful when you resume from a
        previous training and want the directory to look as if the
        training was not interrupted.
        Note that this option does not load old models or any other
        old states for you. It simply does nothing.
    :type action: str, optional
    """

    global LOG_DIR, _FILE_HANDLER, _logger
    if _FILE_HANDLER:
        # unload and close the old file handler, so that we may safely delete the logger directory
        _FILE_HANDLER.close()
        _logger.removeHandler(_FILE_HANDLER)
        del _FILE_HANDLER

    def dir_nonempty(dirname):
        # If directory exists and nonempty (ignore hidden files), prompt for action
        return os.path.isdir(dirname) and len([x for x in os.listdir(dirname) if x[0] != "."])

    if dir_nonempty(dirname):
        if not action:
            _logger.warning(
                """\
Log directory {} exists! Use 'd' to delete it. """.format(
                    dirname
                )
            )
            _logger.warning(
                """\
If you're resuming from a previous run, you can choose to keep it.
Press any other key to exit. """
            )
        while not action:
            action = input("Select Action: k (keep) / d (delete) / q (quit):").lower().strip()
        act = action
        if act == "b":
            backup_name = dirname + _get_time_str()
            shutil.move(dirname, backup_name)
            _logger.info("Directory '{}' backuped to '{}'".format(dirname, backup_name))  # noqa: F821
        elif act == "d":
            shutil.rmtree(dirname, ignore_errors=True)
            if dir_nonempty(dirname):
                shutil.rmtree(dirname, ignore_errors=False)
        elif act == "n":
            dirname = dirname + _get_time_str()
            _logger.info("Use a new log directory {}".format(dirname))  # noqa: F821
        elif act == "k":
            pass
        else:
            raise OSError("Directory {} exits!".format(dirname))
    LOG_DIR = dirname

    def mkdir_p(dirname):
        """Make a dir recursively, but do nothing if the dir exists

        :param dirname: The directory name
        :type dirname: str
        """
        assert dirname is not None
        if dirname == "" or os.path.isdir(dirname):
            return
        try:
            os.makedirs(dirname)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise e

    mkdir_p(dirname)
    _set_file(os.path.join(dirname, "log.log"))


def auto_set_dir(action=None, name=None):
    """
    Use :func:`logger.set_logger_dir` to set log directory to
    "./.aiflows/logs/{scriptname}:{name}". "scriptname" is the name of the main python file currently running

    :param action: an action of ["k","d","q"] to be performed when the directory exists.
        When the directory exists, Will ask user by default.
        -"d": delete the directory. Note that the deletion may fail when
        the directory is used by tensorboard.
        -"k": keep the directory. This is useful when you resume from a
        previous training and want the directory to look as if the
        training was not interrupted.
        Note that this option does not load old models or any other
        old states for you. It simply does nothing.
    :type action: str, optional
    :param name: The name of the directory
    :type name: str, optional
    """
    # Get the directory of the current module
    current_module_file = inspect.getfile(inspect.currentframe())
    current_module_dir = os.path.dirname(os.path.abspath(current_module_file))
    flow_root_dir = os.path.dirname(os.path.dirname(current_module_dir))
    timestamp = _get_time_str()
    auto_dirname = os.path.join(flow_root_dir, "logs", f"{timestamp}")
    if name:
        auto_dirname += "_%s" % name if os.name == "nt" else ":%s" % name
    set_dir(auto_dirname, action=action)


def get_logger_dir():
    """
    :return: The logger directory, or None if not set.
        The directory is used for general logging, tensorboard events, checkpoints, etc.
    :rtype: str
    """
    return LOG_DIR
