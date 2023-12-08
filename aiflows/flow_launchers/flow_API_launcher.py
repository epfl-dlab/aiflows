from abc import ABC

import time
from copy import deepcopy

from typing import Any, List, Dict, Union, Optional, Tuple

import hydra
from omegaconf import DictConfig
from aiflows.base_flows import Flow
from aiflows.flow_launchers import MultiThreadedAPILauncher
from aiflows.messages import InputMessage
from aiflows.interfaces.abstract import Interface
from aiflows.utils import logging

log = logging.get_logger(__name__)


class FlowLauncher(MultiThreadedAPILauncher):
    """Flow Launcher class for running inference on a flow. One can run the inference with the flow launcher in multiple ways:
    - Using the `launch` class method: This method takes a flow and runs inference on the given data (no multithreading) and no need to instantiate the class.
    - Using the `predict_dataloader` method: This method runs inference on the given dataloader (Requires instatiating the class).
    The `predict_dataloader`method can run inference in both single-threaded and multi-threaded modes (see the `MultiThreadedAPILauncher` class for more details).

    :param n_independent_samples: the number of times to independently repeat the same inference for a given sample
    :type n_independent_samples: int
    :param fault_tolerant_mode: whether to crash if an error occurs during the inference for a given sample
    :type fault_tolerant_mode: bool
    :param n_batch_retries: the number of times to retry the batch if an error occurs (only used if `fault_tolerant_mode` is True)
    :type n_batch_retries: int
    :param wait_time_between_retries: the number of seconds to wait before retrying the batch (only used if `fault_tolerant_mode` is True)
    :param \**kwargs: Additional keyword arguments to instantiate the `MultiThreadedAPILauncher` class.
    """

    def __init__(
        self,
        n_independent_samples: int,
        fault_tolerant_mode: bool,
        n_batch_retries: int,
        wait_time_between_retries: int,
        **kwargs,
    ):

        super().__init__(**kwargs)
        self.n_independent_samples = n_independent_samples
        self.fault_tolerant_mode = fault_tolerant_mode
        self.n_batch_retries = n_batch_retries
        self.wait_time_between_retries = wait_time_between_retries
        assert self.n_independent_samples > 0, "The number of independent samples must be greater than 0."

    @staticmethod
    def predict_sample(
        flow: Flow,
        sample: Dict,
        input_interface: Interface = None,
        output_interface: Interface = None,
        fault_tolerant_mode: bool = False,
        n_batch_retries: int = 1,
        wait_time_between_retries: int = 1,
    ) -> Tuple[Dict]:
        """Static method that runs inference on a single sample with a given flow.

        :flow: The flow to run inference with.
        :type flow: Flow
        :sample: The sample to run inference on.
        :type sample: Dict
        :input_interface: The input interface of the flow. Default: None
        :type input_interface: Optional[Interface]
        :output_interface: The output interface of the flow. Default: None
        :type output_interface: Optional[Interface]
        :fault_tolerant_mode: whether to crash if an error occurs during the inference for a given sample. Default: False
        :type fault_tolerant_mode: Optional[bool]
        :n_batch_retries: the number of times to retry the batch if an error occurs (only used if `fault_tolerant_mode` is True). Default: 1
        :type n_batch_retries: Optional[int]
        :wait_time_between_retries: the number of seconds to wait before retrying the batch (only used if `fault_tolerant_mode` is True). Default: 1
        :type wait_time_between_retries: Optional[int]
        :return: A tuple containing the output message, the output data, and the error (if any).
        :rtype: Tuple[Dict]
        """

        if input_interface is not None:
            input_data_dict = input_interface(
                goal="[Input] Run Flow from the Launcher.", data_dict=sample, src_flow=None, dst_flow=flow
            )
        else:
            input_data_dict = sample

        _error = None

        _attempt_idx = 1

        # Should be >1 only if fault_tolerant_mode is True
        n_batch_retries = 1 if not fault_tolerant_mode else n_batch_retries

        while _attempt_idx <= n_batch_retries:
            _error = None
            try:
                input_message = InputMessage.build(data_dict=input_data_dict, src_flow="Launcher", dst_flow=flow.name)

                output_message = flow(input_message)
                output_data = output_message.data["output_data"]

                if output_interface is not None:
                    output_data = output_interface(
                        goal="[Output] Run Flow from the Launcher.", data_dict=output_data, src_flow=flow, dst_flow=None
                    )
                break
            except Exception as e:
                if fault_tolerant_mode:
                    log.error(
                        f"[Problem `{sample['id']}`] "
                        f"Error {_attempt_idx} in running the flow: {e}. "
                        f"Retrying in {wait_time_between_retries} seconds..."
                    )
                    _attempt_idx += 1
                    time.sleep(wait_time_between_retries)
                    _error = str(e)
                else:
                    raise e

        return output_message, output_data, _error

    def predict(
        self,
        batch: List[dict],
    ):
        """Runs inference for the given batch (possibly in a multithreaded fashion). This method is called by the `predict_dataloader`
        method of the `MultiThreadedAPILauncher` class.

        :param batch: The batch to run inference for.
        :type batch: List[dict]
        :return: The batch with the inference outputs added to it.
        :rtype: List[dict]
        """
        assert len(batch) == 1, "The Flow API model does not support batch sizes greater than 1."
        _resource_id = self._resource_IDs.get()  # The ID of the resources to be used by the thread for this sample
        flows_with_interfaces = self.flows[_resource_id]
        flow = flows_with_interfaces["flow"]
        input_interface = flows_with_interfaces["input_interface"]
        output_interface = flows_with_interfaces["output_interface"]
        path_to_output_file = self.paths_to_output_files[_resource_id]
        n_independent_samples = self.n_independent_samples

        batch = self.predict_batch(
            flow=flow,
            input_interface=input_interface,
            output_interface=output_interface,
            batch=batch,
            path_to_output_file=path_to_output_file,
            keys_to_write=["id", "inference_outputs", "human_readable_outputs", "error"],
            n_independent_samples=n_independent_samples,
        )

        self._resource_IDs.put(_resource_id)
        return batch

    @classmethod
    def predict_batch(
        cls,
        flow: Flow,
        batch: List[dict],
        input_interface: Optional[Interface] = None,
        output_interface: Optional[Interface] = None,
        path_to_output_file: Optional[str] = None,
        keys_to_write: Optional[List[str]] = None,
        n_independent_samples: int = 1,
        fault_tolerant_mode: bool = False,
        n_batch_retries: int = 1,
        wait_time_between_retries: int = 1,
    ):
        """Class method that runs inference on the given batch for a given flow.

        :param flow: The flow to run inference with.
        :type flow: Flow
        :param batch: The batch to run inference for.
        :type batch: List[dict]
        :param input_interface: The input interface of the flow. Default: None
        :type input_interface: Optional[Interface]
        :param output_interface: The output interface of the flow. Default: None
        :type output_interface: Optional[Interface]
        :param path_to_output_file: A path to a file to write the outputs to. Default: None
        :type path_to_output_file: Optional[str]
        :param keys_to_write: A list of keys to write to file. Default: None
        :type keys_to_write: Optional[List[str]]
        :param n_independent_samples: the number of times to independently repeat the same inference for a given sample. Default: 1
        :type n_independent_samples: Optional[int]
        :return: The batch with the inference outputs added to it.
        :rtype: List[dict]
        """
        inference_outputs = []
        human_readable_outputs = []
        for sample in batch:
            for _sample_idx in range(n_independent_samples):
                log.info("Running inference for ID (sample {}): {}".format(_sample_idx, sample["id"]))

                output_message, output_data, _error = cls.predict_sample(
                    flow=flow,
                    sample=sample,
                    input_interface=input_interface,
                    output_interface=output_interface,
                    fault_tolerant_mode=fault_tolerant_mode,
                    n_batch_retries=n_batch_retries,
                    wait_time_between_retries=wait_time_between_retries,
                )

                inference_outputs.append(output_message)

                human_readable_outputs.append(output_data)

                if _error is not None:
                    # Break if one of the independent samples failed
                    break
                flow.reset(full_reset=True, recursive=True)  # Reset the flow to its initial state

            sample["inference_outputs"] = inference_outputs

            sample["human_readable_outputs"] = human_readable_outputs

            sample["error"] = _error

        if path_to_output_file is not None:
            cls.write_batch_output(batch, path_to_output_file=path_to_output_file, keys_to_write=keys_to_write)

        return batch

    @classmethod
    def launch(
        cls,
        flow_with_interfaces: Dict[str, Any],
        data: Union[Dict, List[Dict]],
        path_to_output_file: Optional[str] = None,
    ) -> Tuple[List[dict]]:
        """Class method that takes a flow and runs inference on the given data (no multithreading) and no need to instantiate the class.

        :param flow_with_interfaces: A dictionary containing the flow to run inference with and the input and output interfaces to use.
        :type flow_with_interfaces: Dict[str, Any]
        :param data: The data to run inference on.
        :type data: Union[Dict, List[Dict]]
        :param path_to_output_file: A path to a file to write the outputs to.
        :type path_to_output_file: Optional[str], optional
        :return: A tuple containing the full outputs and the human-readable outputs.
        :rtype: Tuple[List[dict]]
        """
        flow = flow_with_interfaces["flow"]
        input_interface = flow_with_interfaces.get("input_interface", None)
        output_interface = flow_with_interfaces.get("output_interface", None)

        if isinstance(data, dict):
            data = [data]

        # data = deepcopy(data) #Would this be necessary? If yes, message nicky
        flow.reset(full_reset=True, recursive=True)

        keys_to_write = ["id", "inference_outputs", "error"]
        data = cls.predict_batch(
            flow=flow,
            input_interface=input_interface,
            output_interface=output_interface,
            batch=data,
            path_to_output_file=path_to_output_file,
            keys_to_write=keys_to_write,
        )
        full_outputs = [{key: sample[key] for key in keys_to_write} for sample in data]
        human_readable_outputs = [sample["human_readable_outputs"] for sample in data]
        return full_outputs, human_readable_outputs
