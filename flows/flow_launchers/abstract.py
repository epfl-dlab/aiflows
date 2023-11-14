import os
import time
from queue import Queue
from concurrent.futures import ThreadPoolExecutor, as_completed

from abc import ABC


from flows.utils import general_helpers
from typing import Any, List, Dict, Optional, Iterable

from ..utils import logging
from ..utils.general_helpers import try_except_decorator
log = logging.get_logger(__name__)


class BaseLauncher(ABC):
    def predict(self, batch: Iterable[Dict]) -> List[Dict]:
        raise NotImplementedError("Not implemented")

    def predict_dataloader(self,
                           dataloader: Iterable,
                           path_to_cache: Optional[str] = None):
        raise NotImplementedError("Not implemented")

    @classmethod
    def _get_outputs_to_write(cls,
                              batch: List[Dict],
                              keys_to_write) -> List[Dict]:
        """
        It takes a batch of predictions and returns a dictionary containing the outputs to write to file.

        Args:
            batch: A list of dictionaries containing the predictions.
            keys_to_write: A list of keys to write to file.


        Returns:
            A dictionary to be written to file.
        """
        to_write_all = []
        for sample in batch:
            to_write_sample = {}

            for key in keys_to_write:
                to_write_sample[key] = sample[key]

            to_write_all.append(to_write_sample)

        return to_write_all

    @classmethod
    def write_batch_output(cls,
                           batch: List[Dict],
                           path_to_output_file: str,
                           keys_to_write: List[str],
                           ):
        batch_output = cls._get_outputs_to_write(batch, keys_to_write)
        general_helpers.write_outputs(path_to_output_file, batch_output, mode="a+")


class  MultiThreadedAPILauncher(BaseLauncher, ABC):
    """
    A class for creating a multi-threaded model to query API that can make requests using multiple API keys.

    Attributes:
        debug: A boolean indicating whether to print debug information (if true, it will not run the multithreading).
        output_dir: The directory to write the output files to.

        api_keys [List(str)]: A list of API keys to use for making requests.
        n_workers_per_key (int): The number of workers to use per API key.
        wait_time_per_key (int): The number of seconds to wait before making another request with the same API key.
        single_threaded : A boolean indicating whether to run the multithreading or not.
    """

    def __init__(self, **kwargs):
        self.n_workers_per_key = kwargs.get("n_workers_per_key", 1)
        
        self.debug = kwargs.get("debug", False)
        self.single_threaded = kwargs.get("single_threaded", False)
        self.output_dir = kwargs.get("output_dir", None)
        #you must specify how many api keys you're using otherwise it defaults to one (affects n_workers used during multithreading)
        self.n_api_keys = kwargs.get("n_api_keys",1) 
        predictions_dir = general_helpers.get_predictions_dir_path(self.output_dir)
        if self.single_threaded:
            self.n_workers = 1
        else:
            self.n_workers = self.n_workers_per_key * self.n_api_keys

        self.paths_to_output_files = []
        _resource_IDs = Queue(self.n_workers)
        for i in range(self.n_workers):
            _resource_IDs.put(i)

            predictions_file = os.path.join(predictions_dir, "predictions_{}.jsonl".format(i))
            self.paths_to_output_files.append(predictions_file)
        self._resource_IDs = _resource_IDs
        self.existing_predictions_file = os.path.join(predictions_dir, "predictions_existing.jsonl")

    
    @try_except_decorator
    def predict_dataloader(self,
                           dataloader: Iterable[dict],
                           flows_with_interfaces: List[Dict[str, Any]],
                           path_to_cache: Optional[str] = None) -> None:
        """
        Runs inference for the data provided in the dataloader.
        It writes the results to output files selected from the output_dir attributes.

        Args:
            dataloader: An iterable of dictionaries containing the data for each sample to run inference on.
            path_to_cache: : A list of existing predictions to use as a starting point.
        """
        self._load_cache(path_to_cache)
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
            log.info(
                "Running in multi-threaded mode with {} keys and {} workers per key.".format(
                    self.n_api_keys, self.n_workers_per_key
                )
            )

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

                        # The goal is to exit the program and not let the thread "handle" an unexpected exception
                        # ToDo: sys.exit(1) vs. os._exit(1): Which one to use? os._exit(1) surely does the job
                        os._exit(1)

        if num_failures > 0:
            log.error("Number of failures: {} (out of {})".format(num_failures, num_datapoints))
