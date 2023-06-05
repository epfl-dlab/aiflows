import logging
import sys

from pytorch_lightning.utilities import rank_zero_only


def get_pylogger(name=__name__, stdout=False) -> logging.Logger:
    """Initializes multi-GPU-friendly python command line logger."""

    if stdout:
        logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

    logger = logging.getLogger(name)

    # this ensures all logging levels get marked with the rank zero decorator
    # otherwise logs would get multiplied for each GPU process in multi-GPU setup
    logging_levels = (
        "debug",
        "info",
        "warning",
        "error",
        "exception",
        "fatal",
        "critical",
    )
    for level in logging_levels:
        setattr(logger, level, rank_zero_only(getattr(logger, level)))

    return logger
