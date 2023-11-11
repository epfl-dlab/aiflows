import copy
from abc import ABC
from typing import List, Dict, Optional, Any

import hydra

from flows.base_flows import Flow

from ..utils import logging

log = logging.get_logger(__name__)


class CompositeFlow(Flow, ABC):
    REQUIRED_KEYS_CONFIG = ["subflows_config"]

    subflows: Dict[str, Flow]

    def __init__(
            self,
            flow_config: Dict[str, Any],
            subflows: List[Flow],
    ):
        super().__init__(flow_config=flow_config,
                         )
        self.subflows = subflows

    @classmethod
    def instantiate_from_config(cls, config):
        flow_config = copy.deepcopy(config)
        return cls(subflows=cls._set_up_subflows(flow_config),
                   flow_config=flow_config,
                   )

    def _call_flow_from_state(
            self,
            goal: str,
            input_interface,
            flow,
            output_interface,
    ):
        """A helper function that calls a given flow by extracting the input data from the state of the current flow."""
        # ~~~ Prepare the data for the call ~~~



        if input_interface is not None:
            payload = input_interface(goal=f"[Input] {goal}",
                                      data_dict=self.flow_state,
                                      src_flow=self,
                                      dst_flow=flow)

        input_message = self._package_input_message(
            payload=payload,
            dst_flow=flow
        )

        # ~~~ Execute the call ~~~
        output_message = flow(input_message)

        # ~~~ Logs the output message to history ~~~
        self._log_message(output_message)

        # ~~~ Process the output ~~~
        output_data = copy.deepcopy(output_message.data["output_data"])
        if output_interface is not None:
            output_data = output_interface(goal=f"[Output] {goal}",
                                           data_dict=output_data,
                                           src_flow=flow,
                                           dst_flow=self)

        return output_message, output_data

    def _get_subflow(self, subflow_name: str) -> Optional[Flow]:
        """Returns the sub-flow with the given name"""
        return self.subflows.get(subflow_name, None)

    @classmethod
    def _set_up_subflows(cls, config):
        subflows = dict()
        subflows_config = config["subflows_config"]

        for subflow_name, subflow_config in subflows_config.items():
            assert "_target_" in subflow_config
            if subflow_config["_target_"].startswith("."):
                cls_parent_module = ".".join(cls.__module__.split(".")[:-1])
                subflow_config["_target_"] = cls_parent_module + subflow_config["_target_"]

            flow_obj = hydra.utils.instantiate(subflow_config, _convert_="partial", _recursive_=False)
            flow_obj.flow_config["name"] = subflow_name
            subflows[subflow_name] = flow_obj

        return subflows

    @classmethod
    def instantiate_from_config(cls, config):
        flow_config = copy.deepcopy(config)

        kwargs = {"flow_config": copy.deepcopy(flow_config)}
        kwargs["subflows"] = cls._set_up_subflows(flow_config)

        return cls(**kwargs)

    def _to_string(self, indent_level=0):
        """Generates a string representation of the flow"""
        indent = "\t" * indent_level
        name = self.flow_config.get("name", "unnamed")
        description = self.flow_config.get("description", "no description")
        input_keys = self.flow_config.get("input_keys", "no input keys")
        output_keys = self.flow_config.get("output_keys", "no output keys")
        class_name = self.__class__.__name__
        subflows_repr = "\n".join([f"{subflow._to_string(indent_level=indent_level + 1)}"
                                   for subflow in [flow for _, flow in self.subflows.items()]])

        entries = [
            f"{indent}Name: {name}",
            f"{indent}Class name: {class_name}",
            f"{indent}Type: {self.type()}",
            f"{indent}Description: {description}",
            f"{indent}Input keys: {input_keys}",
            f"{indent}Output keys: {output_keys}",
            f"{indent}Subflows:",
            f"{subflows_repr}"
        ]
        return "\n".join(entries)

    @classmethod
    def type(cls):
        return "CompositeFlow"
