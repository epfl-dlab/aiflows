import time

from typing import List, Dict

from .collators import Collator, NoCollationCollator
from flows.flow_launcher import MultiThreadedAPILauncher
from flows.base_flows import Flow
from flows.utils import general_helpers
from flows import utils


log = utils.get_pylogger(__name__)


class FlowAPILauncher(MultiThreadedAPILauncher):
    """
    A class for querying the OpenAI API using the LangChain library with interactive chatting capabilities.

    Attributes:
        flow: The flow (or a list of independent instances of the same flow) to run the inference with.
        n_independent_samples: the number of times to independently repeat the same inference for a given sample
        fault_tolerant_mode: whether to crash if an error occurs during the inference for a given sample
        n_batch_retries: the number of times to retry the batch if an error occurs
        wait_time_between_retries: the number of seconds to wait before retrying the batch
        collator: An instance of the Collator class used to prepare the batches
    """

    def __init__(
            self,
            flow: Flow,  # ToDo: This will always be a single flow, no?
            n_independent_samples: int,
            fault_tolerant_mode: bool,
            n_batch_retries: int,
            wait_time_between_retries: int,
            expected_outputs: List[str],
            collator: Collator = None,
            **kwargs,
    ):
        super().__init__(**kwargs)

        if collator is None:
            self.collator = NoCollationCollator()

        self.flow = flow
        self.n_independent_samples = n_independent_samples
        self.fault_tolerant_mode = fault_tolerant_mode
        self.n_batch_retries = n_batch_retries
        self.wait_time_between_retries = wait_time_between_retries
        self.expected_outputs = expected_outputs
        assert self.n_independent_samples > 0, "The number of independent samples must be greater than 0."

    def predict(self, batch: List[Dict]):
        assert len(batch) == 1, "The Flow API model does not support batch sizes greater than 1."
        idx = self._indices.get()

        flow = self.flow[idx]

        output_file = self.output_files[idx]

        for sample in batch:
            log.info("Running inference for sample with ID: {}".format(sample["id"]))
            api_key_idx = self._choose_next_api_key()

            inference_outputs = []
            _success_datapoint = True
            for _ in range(self.n_independent_samples):
                _success_sample = False
                if self.fault_tolerant_mode:
                    attempts = 1

                    while attempts <= self.n_batch_retries:
                        try:
                            # ToDo: package_task_message deep-copies everything, right?
                            # flow.initialize() # ToDo: Remove?
                            sample["api_key"] = self.api_keys[api_key_idx]
                            task_message = flow.package_task_message(recipient_flow=flow,
                                                                     task_name="run_task",
                                                                     task_data=sample,
                                                                     expected_outputs=self.expected_outputs)

                            # self._add_keys_values_input(input_message,
                            #                             kwargs={"api_key": self.api_keys[api_key_idx]})

                            output_message = flow(task_message)

                            inference_outputs.append(output_message.data)  # ToDo: Verify correctness
                            _success_sample = True
                            _error = "None"
                            break
                        except Exception as e:
                            log.error(
                                f"[Problem `{sample['id']}`] "
                                f"Error {attempts} in running the flow: {e}. "
                                f"Retrying in {self.wait_time_between_retries} seconds..."
                            )
                            attempts += 1
                            time.sleep(self.wait_time_between_retries)

                            api_key_idx = self._choose_next_api_key()
                            _error = str(e)

                else:
                    # For debugging purposes
                    sample["api_key"] = self.api_keys[api_key_idx]
                    task_message = flow.package_task_message(recipient_flow=flow,
                                                             task_name="run_task",
                                                             task_data=sample,
                                                             expected_outputs=self.expected_outputs)

                    output_message = flow(task_message)

                    inference_outputs.append(output_message.data)  # ToDo: Verify correctness
                    _success_sample = True
                    _error = "None"

                _success_datapoint = _success_datapoint and _success_sample

            sample["inference_outputs"] = inference_outputs
            sample["success"] = _success_datapoint
            sample["error"] = _error

        if output_file is not None:
            self.write_batch_output(output_file, batch)

        self._indices.put(idx)
        return batch

    def write_batch_output(self, output_file, batch):
        keys_to_write = ["id", "inference_outputs", "success", "error"]
        batch_output = self._get_outputs_to_write(batch, keys_to_write)
        general_helpers.write_outputs(output_file, batch_output, mode="a+")
