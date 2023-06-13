import copy
import time
from typing import List, Dict, Union

from flows.flow_launcher import MultiThreadedAPILauncher

from flows.messages import InputMessage, Message, FlowMessage
from flows.base_flows import Flow

from flows.models.collators import Collator

from flows.utils import general_helpers
from flows import utils
from copy import deepcopy

log = utils.get_pylogger(__name__)


class FlowAPILauncher(MultiThreadedAPILauncher):
    """
    A class for querying the OpenAI API using the LangChain library with interactive chatting capabilities.

    Attributes:
        flow: The flow or a list of flow instances to run the inference with.
        collator: An instance of the Collator class preparing batches.
        n_independent_samples: the number of times to repeat the same prompt to get different examples
        dry_run: A boolean indicating whether the API should be called or not.
    """

    def __init__(
            self,
            flow: Union[Flow, List[Flow]],
            collator: Collator,
            n_independent_samples: int,
            **kwargs,
    ):
        super().__init__(**kwargs)

        self.flow = flow
        self.collator = collator
        self.n_independent_samples = n_independent_samples
        self.fault_tolerant_mode = kwargs["fault_tolerant_mode"]
        self.n_batch_retries = kwargs["n_batch_retries"]
        self.wait_time_between_retries = kwargs["wait_time_between_retries"]
        assert self.n_independent_samples > 0, "The number of independent samples must be greater than 0."

    @staticmethod
    def _build_input_message(sample: Dict, flow: Flow) -> InputMessage:
        launcher_flow_run_id = utils.general_helpers.create_unique_id()
        inputs = {k: FlowMessage(
            content=sample[k],
            message_creator="task-launcher",
            flow_run_id=launcher_flow_run_id,
            parents=[])
            for k in flow.expected_inputs
        }

        inp = InputMessage(
            inputs=inputs,
            content="Intial input message",
            message_creator="task-launcher",
            flow_run_id=launcher_flow_run_id,
            target_flow=flow.flow_run_id,
            parents=[]
        )
        return inp

    @staticmethod
    def _add_keys_values_input(input_message: InputMessage, kwargs):
        for key, val in kwargs.items():
            input_message.inputs[key] = FlowMessage(
                content=val,
                message_creator="task-launcher",
                flow_run_id=input_message.flow_run_id,
                parents=[]
            )

    def predict(self, batch: List[Dict]):
        assert len(batch) == 1, "The Flow API model does not support batch sizes greater than 1."
        idx = self._indices.get()

        flow = self.flow[idx]

        output_file = self.output_files[idx]

        for sample in batch:
            log.info("Running inference for sample with ID: {}".format(sample["id"]))
            api_key_idx = self._choose_next_api_key()
            input_message = self._build_input_message(sample, flow)

            inference_outputs = []
            _success_datapoint = True
            for _ in range(self.n_independent_samples):
                _success_sample = False
                if self.fault_tolerant_mode:
                    attempts = 1

                    while attempts <= self.n_batch_retries:
                        try:
                            self._add_keys_values_input(input_message, kwargs={"api_key": self.api_keys[api_key_idx],
                                                                               "dry_run": False})
                            inference_output = flow.run(deepcopy(input_message))

                            inference_outputs.append(deepcopy(inference_output))
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
                    flow.initialize()

                    self._add_keys_values_input(input_message, kwargs={"api_key": self.api_keys[api_key_idx],
                                                                       "dry_run": False})

                    inference_output = flow.run(deepcopy(input_message))
                    inference_outputs.append(deepcopy(inference_output))
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
