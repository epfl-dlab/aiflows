import inspect
import os
import shutil
import unittest

from ..flows.utils import logging

log = logging.get_logger()  # get the root logger of library


class LoggingModuleTests(unittest.TestCase):
    def test_change_log_level(self) -> None:
        logging.set_verbosity_debug()
        log = logging.get_logger()
        self.assertEquals(log.level, logging.DEBUG)

    def test_logging_after_changing_log_level(self) -> None:
        logging.set_verbosity_info()
        print("You should see a test message at each log level, including debug: ")
        log.info("This is a test message at info level")
        log.debug("This is a test message at debug level")
        log.warning("This is a test message at warning level")
        log.error("This is a test message at error level")
        log.critical("This is a test message at critical level")

    def test_change_log_level_back(self) -> None:
        logging.set_verbosity_warning()
        print("You should see a test message at each log level, except for debug and info: ")
        log.info("This is a test message at info level")
        log.debug("This is a test message at debug level")
        log.warning("This is a test message at warning level")
        log.error("This is a test message at error level")
        log.critical("This is a test message at critical level")
        self.assertEquals(log.level, logging.WARNING)

    def test_logging_to_file(self) -> None:
        # shutil.rmtree(os.path.join(logging.LOG_DIR))
        current_module_file = inspect.getfile(inspect.currentframe())
        current_module_dir = os.path.dirname(os.path.abspath(current_module_file))
        default_log_dir = os.path.join(os.path.dirname(current_module_dir), "logs")

        # clean up the default log dir if it exists
        if os.path.exists(default_log_dir):
            shutil.rmtree(default_log_dir)

        logging.auto_set_dir()  # by default, the logs are written to the root directory of the flows library
        logger = logging.get_logger()
        logger.info("INFO")
        logger.warning("WARN")

        # check that the logs are written to the default log dir
        self.assertTrue(os.path.exists(default_log_dir))
        shutil.rmtree(default_log_dir)

    def test_logging_to_custom_log_dir(self) -> None:
        import tempfile

        # Get the current temporary directory
        tmp_dir = tempfile.mkdtemp()

        # Print the temporary directory
        print(tmp_dir)

        custom_log_dir = tmp_dir
        logging.set_dir(custom_log_dir)
        logger = logging.get_logger()
        logger.info("INFO")
        logger.warning("WARN")
        self.assertTrue(os.path.exists(custom_log_dir))
        shutil.rmtree(custom_log_dir)


if __name__ == "__main__":
    unittest.main()
