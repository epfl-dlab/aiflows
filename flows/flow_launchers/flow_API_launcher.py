from abc import ABC

import time

from typing import List, Dict, Union, Optional

import flows.base_flows
from flows.flow_launchers import MultiThreadedAPILauncher
from flows.base_flows import Flow
from flows import utils


log = utils.get_pylogger(__name__)


class FlowLauncher(ABC):
    def __init__(
            self,
            flow: Flow,
            output_keys: Optional[List[str]] = None) -> None:
        
        self.flow = flow
        self.output_keys = output_keys

    def launch(self, inputs: List[Dict]) -> List[Dict]:
        outputs = []
        for sample in inputs:
            self.flow.reset(full_reset=True, recursive=True)  # Reset the flow to its initial state

            input_message = self.flow.package_input_message(data=sample,
                                                        src_flow="Launcher",
                                                        output_keys=self.output_keys)
            output_message = self.flow(input_message)
            outputs.append(output_message.data["outputs"])

        return outputs



class FlowAPILauncher(MultiThreadedAPILauncher):
    """
    A class for querying the OpenAI API using the LangChain library with interactive chatting capabilities.

    Attributes:
        flow: The flow (or a list of independent instances of the same flow) to run the inference with.
        n_independent_samples: the number of times to independently repeat the same inference for a given sample
        fault_tolerant_mode: whether to crash if an error occurs during the inference for a given sample
        n_batch_retries: the number of times to retry the batch if an error occurs
        wait_time_between_retries: the number of seconds to wait before retrying the batch
    """

    def __init__(
            self,
            flow: Union[Flow, List[Flow]], # TODO(yeeef): not good for a list of flows which is of same class
            n_independent_samples: int,
            fault_tolerant_mode: bool,
            n_batch_retries: int,
            wait_time_between_retries: int,
            output_keys: List[str],
            **kwargs,
    ):
        super().__init__(**kwargs)

        if isinstance(flow, Flow):
            flow = [flow]

        self.flows = flow

        assert self.n_workers == len(self.flows), "FlowAPILauncher must be given as many flows as workers. " \
                                                  "# of flows passed: {}, # of workers: {}".format(len(self.flows),
                                                                                                   self.n_workers)

        self.n_independent_samples = n_independent_samples
        self.fault_tolerant_mode = fault_tolerant_mode
        self.n_batch_retries = n_batch_retries
        self.wait_time_between_retries = wait_time_between_retries
        self.output_keys = output_keys
        assert self.n_independent_samples > 0, "The number of independent samples must be greater than 0."

    def _load_cache(self, path_to_cache):
        # ToDo: implement cache loading
        # ToDo: Add tests to verify that the resuming option works both in single_threaded and multi_threaded mode
        pass

    def predict(self, batch: List[Dict]):
        # ToDo: pass the cache in the expected way to the flow

        assert len(batch) == 1, "The Flow API model does not support batch sizes greater than 1."
        _resource_id = self._resource_IDs.get()  # The ID of the resources to be used by the thread for this sample
        flow = self.flows[_resource_id]
        path_to_output_file = self.paths_to_output_files[_resource_id]

        for sample in batch:
            inference_outputs = []
            _error = None
            for _sample_idx in range(self.n_independent_samples):
                log.info("Running inference for ID (sample {}): {}".format(_sample_idx, sample["id"]))
                api_key_idx = self._choose_next_api_key()
                _error = None
                flow.reset(full_reset=True, recursive=True)  # Reset the flow to its initial state

                if self.fault_tolerant_mode:
                    _attempt_idx = 1

                    while _attempt_idx <= self.n_batch_retries:
                        try:
                            api_keys = {"openai": self.api_keys[api_key_idx]}
                            input_message = flow.package_input_message(data=sample,
                                                                       src_flow="Launcher",
                                                                       output_keys=self.output_keys,
                                                                       api_keys=api_keys)
                            # ToDO: Add private_keys and keys_to_ignore_for_hash to the Launcher config and pass to package_input_message

                            output_message = flow(input_message)

                            inference_outputs.append(output_message.data)
                            _success_sample = True
                            _error = None
                            break
                        except Exception as e:
                            log.error(
                                f"[Problem `{sample['id']}`] "
                                f"Error {_attempt_idx} in running the flow: {e}. "
                                f"Retrying in {self.wait_time_between_retries} seconds..."
                            )
                            _attempt_idx += 1
                            time.sleep(self.wait_time_between_retries)

                            api_key_idx = self._choose_next_api_key()
                            _error = str(e)

                else:
                    # For development and debugging purposes
                    api_keys = {"openai": self.api_keys[api_key_idx]}
                    input_message = flow.package_input_message(data_dict=sample,
                                                               src_flow="Launcher",
                                                               output_keys=self.output_keys,
                                                               api_keys=api_keys)
                    output_message = flow(input_message)

                    inference_outputs.append(output_message)
                    _error = None

                if _error is not None:
                    # Break if one of the independent samples failed
                    break

            sample["inference_outputs"] = inference_outputs
            # ToDo: how is None written/loaded to/from a JSON file --> Mention this in the documentation and remove ToDo
            sample["error"] = _error

        self.write_batch_output(batch,
                                path_to_output_file=path_to_output_file,
                                keys_to_write=["id",
                                               "inference_outputs",
                                               "error"])

        self._resource_IDs.put(_resource_id)
        return batch
