import os, sys
import time
from queue import Queue
from concurrent.futures import ThreadPoolExecutor, as_completed

from abc import ABC

from tqdm import tqdm

from flows.utils import general_helpers
from torch.utils.data.dataloader import DataLoader
from typing import List, Dict, Optional, Union

from flows import utils

log = utils.get_pylogger(__name__)


class BaseLauncher(ABC):
    def predict(self, batch: List[Dict]) -> List[Dict]:
        raise NotImplementedError("Not implemented")

    def predict_dataloader(self, dataloader: DataLoader, existing_predictions: List = None):
        raise NotImplementedError("Not implemented")

    @staticmethod
    def _get_outputs_to_write(batch: List[Dict], keys_to_write: Optional[List] = None) -> List[Dict]:
        """
        It takes a batch of predictions and returns a dictionary containing the outputs to write to file.

        Args:
            batch (list): A list of dictionaries containing the predictions.

        Returns:
            A dictionary containing the outputs to write to file.
        """

        if keys_to_write is None:
            keys_to_write = ["id", "inference_outputs"]

        to_write_all = []
        for sample in batch:
            to_write_sample = {}

            for key in keys_to_write:
                # ToDo: remove after finishing the CF existing runs
                if key == "success" and key not in sample:
                    to_write_sample[key] = True
                elif key == "error" and key not in sample:
                    to_write_sample[key] = "None"
                else:
                    to_write_sample[key] = sample[key]

            to_write_all.append(to_write_sample)

        return to_write_all


class MultiThreadedAPILauncher(BaseLauncher, ABC):
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
        self.api_keys = kwargs["api_keys"]
        self.n_workers_per_key = kwargs.get("n_workers_per_key", 1)
        self.__waittime_per_key = kwargs.get("wait_time_per_key", 6)
        # Initialize to now - waittime_per_key to make the class know we haven't called it recently
        self.__last_call_per_key = [time.time() - self.__waittime_per_key] * len(self.api_keys)

        self.debug = kwargs.get("debug", False)
        self.single_threaded = kwargs.get("single_threaded", False)
        self.output_dir = kwargs.get("output_dir", None)

        predictions_dir = general_helpers.get_predictions_dir_path(self.output_dir)
        if self.single_threaded:
            self.n_workers = 1
        else:
            self.n_workers = self.n_workers_per_key * len(self.api_keys)

        self.output_files = []
        _indices = Queue(self.n_workers)
        for i in range(self.n_workers):
            _indices.put(i)

            predictions_file = os.path.join(predictions_dir, "predictions_{}.jsonl".format(i))
            self.output_files.append(predictions_file)
        self._indices = _indices
        self.existing_predictions_file = os.path.join(predictions_dir, "predictions_existing.jsonl")

    def _choose_next_api_key(self) -> int:
        """
        It chooses the next API key to use, by:
        - finding the one that has been used the least recently
        - check whether we need to wait for using it or not
        - if we don't need to wait, we use this key
        - if we need to wait, we wait the appropriate amount of time and retry to find a key

        Why retry instead of using the key we were waiting for after waiting?
        Because another thread might have taken this key and another one might have become available in the meantime.

        Returns:
            api_key_index, the index of the key to using next
        """
        api_key_idx = self.__last_call_per_key.index(min(self.__last_call_per_key))
        last_call_on_key = time.time() - self.__last_call_per_key[api_key_idx]
        good_to_go = last_call_on_key > self.__waittime_per_key

        if not good_to_go:
            time.sleep(self.__waittime_per_key - last_call_on_key)
            return self._choose_next_api_key()

        self.__last_call_per_key[api_key_idx] = time.time()
        return api_key_idx

    def predict_dataloader(self, dataloader: DataLoader, existing_predictions: Union[List, None] = None) -> None:
        """
        Make predictions from a pytorch dataloader using multiple workers.
        It writes the results to output files selected from the output_dir attributes.

        Args:
            dataloader (DataLoader): A PyTorch DataLoader object that provides the input data.
            existing_predictions (List): A list of existing predictions to use as a starting point.
        """
        if existing_predictions is not None:
            id2existing_predictions = {sample["id"]: sample for sample in existing_predictions}

            # self.write_batch_output(output_file=self.existing_predictions_file, batch=existing_predictions)
            # existing_predictions_ids = set([sample["id"] for sample in existing_predictions])
        else:
            id2existing_predictions = {}

        num_datapoints = 0
        num_failures = 0

        if self.debug or self.single_threaded:
            log.info("Running in single-threaded mode.")

            with tqdm(total=len(dataloader)) as pbar:
                for batch in tqdm(dataloader):
                    if batch[0]["id"] in id2existing_predictions:
                        log.info("SKIPPING problem with ID {} -- predictions already exist".format(batch[0]["id"]))
                        self.write_batch_output(
                            output_file=self.existing_predictions_file, batch=[id2existing_predictions[batch[0]["id"]]]
                        )
                        continue

                    batch = self.predict(batch=batch)
                    num_datapoints += len(batch)
                    num_failures += len([sample for sample in batch if not sample["success"]])
                    pbar.update(1)
        else:
            log.info(
                "Running in multi-threaded mode with {} keys and {} workers per key.".format(
                    len(self.api_keys), self.n_workers_per_key
                )
            )

            # with tqdm(total=len(dataloader)) as pbar:
            c = 0
            total = len(dataloader)

            with ThreadPoolExecutor(max_workers=self.n_workers) as executor:
                futures = []

                for batch in dataloader:
                    if batch[0]["id"] in id2existing_predictions:
                        c = c + 1
                        log.info("SKIPPING problem with ID {} -- predictions already exist".format(batch[0]["id"]))
                        log.info("~~~~~~~~~~~~ Progress: {}/{} batches finished ~~~~~~~~~~~~~".format(c, total))
                        self.write_batch_output(
                            output_file=self.existing_predictions_file,
                            batch=[id2existing_predictions[batch[0]["id"]]]
                        )
                        continue

                    futures.append(executor.submit(self.predict, batch=batch))

                for future in as_completed(futures):
                    c = c + 1
                    log.info("~~~~~~~~~~~~ Progress: {}/{} batches finished ~~~~~~~~~~~~~".format(c, total))
                    # pbar.update(1)
                    try:
                        batch = future.result()
                        num_datapoints += len(batch)
                        num_failures += len([sample for sample in batch if not sample["success"]])
                    except Exception as e:
                        log.exception("")
                        # ToDo: do we really want os._exit(1) here?
                        # I don't see a way to test this, since it kills the python process entirely
                        sys.exit(1)

        if num_failures > 0:
            log.error("Number of failures: {} (out of {})".format(num_failures, num_datapoints))
