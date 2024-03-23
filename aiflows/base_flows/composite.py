import copy
from abc import ABC
from typing import List, Dict, Optional, Any,Union

import hydra

from aiflows.base_flows import Flow

from ..utils import logging

log = logging.get_logger(__name__)


class CompositeFlow(Flow, ABC):
    """This class implements a composite flow. It is a flow that consists of multiple sub-flows.
    It is the a parent class for BranchingFlow, SequentialFlow and CircularFlow. Note that the run method of a CompositeFlow is not implemented.

    :param flow_config: The configuration of the flow. It must usually contain the following keys:
        - "subflows_config" (Dict[str,Any]): A dictionary of subflows configurations.The keys are the names of the subflows and the values are the configurations of the subflows.
        This is necessary when instantiating the flow from a config file.
        - The parameters required by the constructor of the parent class Flow
    :type flow_config: Dict[str, Any]
    :param subflows: A list of subflows. This is necessary when instantiating the flow programmatically.
    :type subflows: List[Flow]
    """

    REQUIRED_KEYS_CONFIG = ["subflows_config"]

    subflows: Dict[str, Flow]

    def __init__(
        self,
        flow_config: Dict[str, Any],
        subflows: List[Flow],
    ):
        super().__init__(
            flow_config=flow_config,
        )
        self.subflows = subflows

    @classmethod
    def instantiate_from_config(cls, config):
        """Instantiates the flow from a config file.

        :param config: The configuration of the flow. It must usually contain the following keys:
            - "subflows_config" (Dict[str,Any]): A dictionary of subflows configurations.The keys are the names of the subflows and the values are the configurations of the subflows.
                                                    This is necessary when instantiating the flow from a config file.
            - The parameters required by the constructor of the parent class Flow
        :type config: Dict[str, Any]
        :return: The instantiated flow
        :rtype: CompositeFlow
        """
        flow_config = copy.deepcopy(config)
        return cls(
            subflows=cls._set_up_subflows(flow_config),
            flow_config=flow_config,
        )
    
    def _get_subflow(self, subflow_name: str) -> Optional[Flow]:
        """Returns the sub-flow with the given name

        :param subflow_name: The name of the sub-flow
        :type subflow_name: str
        :return: The sub-flow with the given name
        :rtype: Optional[Flow]
        """
        return self.subflows.get(subflow_name, None)

    @classmethod
    def _set_up_subflows(cls, config):
        """Instantiates the subflows from their configurations.

        :param config: The configuration of the flow. It must usually contain the following keys:
            - "subflows_config" (Dict[str,Any]): A dictionary of subflows configurations.The keys are the names of the subflows and the values are the configurations of the subflows.
            This is necessary when instantiating the flow from a config file.
        :type config: Dict[str, Any]
        :return: A dictionary of subflows. The keys are the names of the subflows and the values are the subflows.
        :rtype: Dict[str, Flow]
        """
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
        """Instantiates the flow from a config file.

        :param config: The configuration of the flow. It must usually contain the following keys:
            - "subflows_config" (Dict[str,Any]): A dictionary of subflows configurations.The keys are the names of the subflows and the values are the configurations of the subflows.
            This is necessary when instantiating the flow from a config file.
            - The parameters required by the constructor of the parent class Flow
        """
        flow_config = copy.deepcopy(config)

        kwargs = {"flow_config": copy.deepcopy(flow_config)}
        kwargs["subflows"] = cls._set_up_subflows(flow_config)

        return cls(**kwargs)

    def _to_string(self, indent_level=0):
        """Generates a string representation of the flow

        :param indent_level: The indentation level of the string representation, defaults to 0
        :type indent_level: int, optional
        :return: The string representation of the flow
        :rtype: str
        """
        indent = "\t" * indent_level
        name = self.flow_config.get("name", "unnamed")
        description = self.flow_config.get("description", "no description")
        input_keys = self.flow_config.get("input_keys", "no input keys")
        output_keys = self.flow_config.get("output_keys", "no output keys")
        class_name = self.__class__.__name__
        subflows_repr = "\n".join(
            [
                f"{subflow._to_string(indent_level=indent_level + 1)}"
                for subflow in [flow for _, flow in self.subflows.items()]
            ]
        )

        entries = [
            f"{indent}Name: {name}",
            f"{indent}Class name: {class_name}",
            f"{indent}Type: {self.type()}",
            f"{indent}Description: {description}",
            f"{indent}Input keys: {input_keys}",
            f"{indent}Output keys: {output_keys}",
            f"{indent}Subflows:",
            f"{subflows_repr}",
        ]
        return "\n".join(entries)

    @classmethod
    def type(cls):
        """Returns the type of the flow as a string."""
        return "CompositeFlow"
