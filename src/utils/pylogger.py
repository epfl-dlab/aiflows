import logging
import sys


def get_pylogger(name=__name__, stdout=False) -> logging.Logger:
    if stdout:
        logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

    logger = logging.getLogger(name)
    return logger
