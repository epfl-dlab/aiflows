import os
import time
from queue import Queue
from concurrent.futures import ThreadPoolExecutor, as_completed

from abc import ABC

from aiflows.utils import general_helpers
from typing import Any, List, Dict, Optional, Iterable

from aiflows.utils import logging

log = logging.get_logger(__name__)


class BaseLauncher(ABC):
    """A base class for creating a model launcher."""

    def predict(self, batch: Iterable[Dict]) -> List[Dict]:
        """Runs inference for the data provided in the batch. It returns a list of dictionaries containing the predictions. (Not Implemented for BaseLauncher)

        :param batch: An iterable of dictionaries containing the data for each sample to run inference on.
        :type batch: Iterable[Dict]
        :return: A list of dictionaries containing the predictions.
        :rtype: List[Dict]
        """
        raise NotImplementedError("Not implemented")

    def predict_dataloader(self, dataloader: Iterable, path_to_cache: Optional[str] = None):
        """Runs inference for the data provided in the dataloader. (Not Implemented for BaseLauncher)

        :param dataloader: An iterable of dictionaries containing the data for each sample to run inference on.
        :type dataloader: Iterable
        :param path_to_cache: A path to a cache file containing existing predictions to use as a starting point.
        :type path_to_cache: Optional[str], optional
        """
        raise NotImplementedError("Not implemented")

    @classmethod
    def _get_outputs_to_write(cls, batch: List[Dict], keys_to_write) -> List[Dict]:
        """
        Class method that takes a batch of predictions and returns a dictionary containing the outputs to write to file.

        :param batch: A list of dictionaries containing the predictions.
        :type batch: List[Dict]
        :param keys_to_write: A list of keys to write to file.
        :type keys_to_write: List[str]
        :return: A dictionary to be written to file.
        :rtype: List[Dict]
        """
        to_write_all = []
        for sample in batch:
            to_write_sample = {}

            for key in keys_to_write:
                to_write_sample[key] = sample[key]

            to_write_all.append(to_write_sample)

        return to_write_all

    @classmethod
    def write_batch_output(
        cls,
        batch: List[Dict],
        path_to_output_file: str,
        keys_to_write: List[str],
    ):
        """Class method that writes the output of a batch to a file.

        :param batch: A list of dictionaries containing the predictions.
        :type batch: List[Dict]
        :param path_to_output_file: The path to the output file.
        :type path_to_output_file: str
        :param keys_to_write: A list of keys to write to file.
        :type keys_to_write: List[str]
        """
        batch_output = cls._get_outputs_to_write(batch, keys_to_write)
        general_helpers.write_outputs(path_to_output_file, batch_output, mode="a+")


class MultiThreadedAPILauncher(BaseLauncher, ABC):
    """
    A class for creating a multi-threaded model to query API that can make requests using multiple API keys.

    :param debug: A boolean indicating whether to print debug information (if true, it will not run the multithreading).
    :type debug: bool, optional
    :param output_dir: The directory to write the output files to.
    :type output_dir: str, optional
    :param n_workers: The number of workers to use in the multithreading.
    :type n_workers: int, optional
    :param wait_time_per_key: The number of seconds to wait before making another request with the same API key.
    :type wait_time_per_key: int, optional
    :param single_threaded: A boolean indicating whether to run the multithreading or not.
    :type single_threaded: bool, optional
    """

    def __init__(self, **kwargs):
        self.n_workers = kwargs.get("n_workers", 1)

        self.debug = kwargs.get("debug", False)
        self.single_threaded = kwargs.get("single_threaded", False)
        self.output_dir = kwargs.get("output_dir", None)
        # you must specify how many api keys you're using otherwise it defaults to one (affects n_workers used during multithreading)
        predictions_dir = general_helpers.get_predictions_dir_path(self.output_dir)
        if self.single_threaded:
            self.n_workers = 1

        self.paths_to_output_files = []
        _resource_IDs = Queue(self.n_workers)
        for i in range(self.n_workers):
            _resource_IDs.put(i)

            predictions_file = os.path.join(predictions_dir, "predictions_{}.jsonl".format(i))
            self.paths_to_output_files.append(predictions_file)
        self._resource_IDs = _resource_IDs
        self.existing_predictions_file = os.path.join(predictions_dir, "predictions_existing.jsonl")

    def predict_dataloader(self, dataloader: Iterable[dict], flows_with_interfaces: List[Dict[str, Any]]) -> None:
        """
        Runs inference for the data provided in the dataloader.
        It writes the results to output files selected from the output_dir attributes.

        :param dataloader: An iterable of dictionaries containing the data for each sample to run inference on.
        :param flows_with_interfaces(List[Dict]): A list of dictionaries containing a flow instance, and an input and output interface.
        """
        self.flows = flows_with_interfaces

        num_datapoints = len(dataloader)
        num_failures = 0

        if self.debug or self.single_threaded:
            log.info("Running in single-threaded mode.")

            c = 0
            for sample in dataloader:
                sample = self.predict(batch=[sample])[0]
                if sample["error"] is not None:
                    num_failures += 1
                c += 1
                log.info("~~~~~~~~~~~~ Progress: {}/{} batches finished ~~~~~~~~~~~~~".format(c, num_datapoints))
        else:
            log.info("Running in multi-threaded mode with {} workers.".format(self.n_workers))

            c = 0

            with ThreadPoolExecutor(max_workers=self.n_workers) as executor:
                futures = []

                for sample in dataloader:
                    futures.append(executor.submit(self.predict, batch=[sample]))

                for future in as_completed(futures):
                    c = c + 1
                    log.info("~~~~~~~~~~~~ Progress: {}/{} batches finished ~~~~~~~~~~~~~".format(c, num_datapoints))
                    try:
                        sample = future.result()[0]
                        if sample["error"] is not None:
                            num_failures += 1
                    except Exception as e:
                        log.exception("")  # logs the exception
                        os._exit(1)

        if num_failures > 0:
            log.error("Number of failures: {} (out of {})".format(num_failures, num_datapoints))
