from typing import List, Dict, Any, Union

import hydra

import aiflows.interfaces
from aiflows.base_flows import CompositeFlow, Flow
from aiflows.data_transformations.abstract import DataTransformation

from ..utils import logging

log = logging.get_logger(__name__)


class TopologyNode:
    """This class represents a node in the topology of a flows.

    :param goal: The goal of the node
    :type goal: str
    :param input_interface: The input interface of the node's flow
    :type input_interface: aiflows.interfaces.InputInterface
    :param flow: The flow of the node
    :type flow: aiflows.base_flows.Flow
    :param output_interface: The output interface of the node's flow
    :type output_interface: List[aiflows.data_transformations.DataTransformation]
    :param reset: Whether to reset the node's flow
    :type reset: bool
    """

    def __init__(
        self, goal, input_interface, flow: Flow, output_interface: List[DataTransformation], reset: bool
    ) -> None:
        self.goal = goal
        self.input_interface = input_interface
        self.flow = flow
        self.output_interface = output_interface
        self.reset = reset


class CircularFlow(CompositeFlow):
    """This class represents a circular flow. It is a composite flow that runs its subflows in a circular fashion.

    :param flow_config: The flow configuration dictionary. It must usually should contain the following keys:
                        - 'max_rounds' (int): The maximum number of rounds to run the circular flow
                        - 'early_exit_key' (str): The key in the flow state that indicates the end of the interaction
                        - 'topology' (list[Dict[str, Any]]): The topology of the circular flow (the dictionary describes the topology of one node, see TopologyNode for details)
                        - The keys required by CompositeFlow (subflows_config)
    :type flow_config: Dict[str, Any]
    :param subflows: A list of subflows. This is necessary when instantiating the flow programmatically.
    :type subflows: List[aiflows.base_flows.Flow]   
    :param max_rounds: The maximum number of rounds to run the circular flow
    :type max_rounds: int
    :topology: The topology of the circular flow
    :type topology: List[TopologyNode]   
    """

    REQUIRED_KEYS_CONFIG = ["max_rounds", "early_exit_key", "topology"]

    __default_flow_config = {"max_rounds": 3, "early_exit_key": "EARLY_EXIT", "topology": []}

    __input_msg_payload_builder_registry = {}
    __output_msg_payload_processor_registry = {}

    @staticmethod
    def input_msg_payload_builder(builder_fn):
        """This decorator registers a function as an input message payload builder.

        :param builder_fn: The function to register
        :type builder_fn: Callable
        :return: The wrapped function
        :rtype: Callable
        """

        def wrapper(goal, data_dict, src_flow: Flow, dst_flow: Flow):
            return builder_fn(src_flow, data_dict, dst_flow)

        CircularFlow.__input_msg_payload_builder_registry[builder_fn.__qualname__] = wrapper
        log.debug(f"input_msg_payload_builder [{builder_fn.__qualname__}] registered")
        return wrapper

    @staticmethod
    def output_msg_payload_processor(processor_fn):
        """This decorator registers a function as an output message payload processor.

        :param processor_fn: The function to register
        :type processor_fn: Callable
        :return: The wrapped function
        :rtype: Callable
        """

        def wrapper(goal, data_dict, src_flow, dst_flow):
            return processor_fn(dst_flow, data_dict, src_flow)

        CircularFlow.__output_msg_payload_processor_registry[processor_fn.__qualname__] = wrapper
        log.debug(f"output_msg_payload_processor [{processor_fn.__qualname__}] registered")
        return wrapper

    def __init__(
        self,
        flow_config: Dict[str, Any],
        subflows: List[Flow],
    ):
        super().__init__(flow_config=flow_config, subflows=subflows)
        if len(self.subflows) <= 0:
            raise ValueError(f"Circular flow needs at least one subflow, currently has 0")
        self.topology = self.__set_up_topology()

    def _early_exit(self):
        """Checks whether the early exit condition is met.

        :return: Whether the early exit condition is met
        :rtype: bool
        """
        early_exit_key = self.flow_config.get("early_exit_key", None)
        if early_exit_key:
            if early_exit_key in self.flow_state:
                return bool(self.flow_state[early_exit_key])
            elif early_exit_key in self.__dict__:
                return bool(self.__dict__[early_exit_key])

        return False

    def __set_up_topology(self) -> List[TopologyNode]:
        """Sets up the topology of the circular flow.

        :return: The topology of the circular flow
        :rtype: List[TopologyNode]
        """
        topology = self.flow_config.get("topology", [])
        ret = []
        if len(topology) == 0:
            raise ValueError(f"topology is empty for flow {self.flow_config['name']}")

        # parse topology
        for topo_config in topology:
            flow_name = topo_config["flow"]
            if flow_name not in self.subflows:
                raise ValueError(f"flow {flow_name} is not in subflow_configs")

            flow = self.subflows[flow_name]
            reset = topo_config.get("reset", False)
            input_interface = topo_config.get("input_interface", None)
            if input_interface is not None:
                # first search _input_msg_payload_builder_registry
                if input_interface["_target_"].startswith("."):
                    registry_key = self.__class__.__name__ + "." + input_interface["_target_"]
                else:
                    registry_key = input_interface["_target_"]
                # log.debug(f"registry_key: {registry_key}")
                if registry_key in CircularFlow.__input_msg_payload_builder_registry:
                    input_interface = CircularFlow.__input_msg_payload_builder_registry[registry_key]
                else:
                    input_interface = hydra.utils.instantiate(input_interface, _recursive_=False, _convert_="partial")
            else:
                input_interface = aiflows.interfaces.KeyInterface()
                input_interface.transformations.append(aiflows.data_transformations.KeyMatchInput())

            output_interface = topo_config.get("output_interface", None)
            if output_interface is not None:
                # first search _output_msg_payload_processor_registry
                if output_interface["_target_"].startswith("."):
                    registry_key = self.__class__.__name__ + output_interface["_target_"]
                else:
                    registry_key = output_interface["_target_"]
                # log.debug(f"registry_key: {registry_key}")
                if registry_key in CircularFlow.__output_msg_payload_processor_registry:
                    output_interface = CircularFlow.__output_msg_payload_processor_registry[registry_key]
                else:
                    output_interface = hydra.utils.instantiate(output_interface, _recursive_=False, _convert_="partial")

            ret.append(
                TopologyNode(
                    goal=topo_config["goal"],
                    input_interface=input_interface,
                    flow=flow,
                    output_interface=output_interface,
                    reset=reset,
                )
            )

        return ret

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Runs the circular flow. It runs its subflows in a circular fashion (following the topology).

        :param input_data: The input data dictionary
        :type input_data: Dict[str, Any]
        :return: The output data dictionary
        :rtype: Dict[str, Any]
        """
        # ~~~ sets the input_data in the flow_state dict ~~~
        self._state_update_dict(update_data=input_data)

        max_rounds = self.flow_config.get("max_rounds", 1)
        if max_rounds is None:
            log.info(f"Running {self.flow_config['name']} without `max_rounds` until the early exit condition is met.")

        self._sequential_run(max_rounds=max_rounds)

        output = self._get_output_from_state()

        return output

    def _get_output_from_state(self):
        """Returns the output from the flow state.

        :return: The output from the flow state
        :rtype: Dict[str, Any]
        """
        outputs = self._fetch_state_attributes_by_keys(keys=self.get_interface_description()["output"])
        return outputs

    @classmethod
    def type(cls):
        """Returns the type of the flow as a string."""
        return "circular"

    def _on_reach_max_rounds(self):
        """Called when the maximum number of rounds is reached"""
        log.info(f"[{self.flow_config['name']}] Max rounds reached. Returning output, answer might be incomplete.")
        return

    def _sequential_run(self, max_rounds: Union[int, None]):
        """Runs the circular flow in a sequential fashion. It runs its subflows in a circular fashion (following the topology).
        It stops when the maximum number of rounds is reached or the early exit condition is met.

        :param max_rounds: The maximum number of rounds to run the circular flow
        :type max_rounds: Union[int, None]
        :return: The output data dictionary
        """
        curr_round = 0
        while max_rounds is None or curr_round < max_rounds:
            curr_round += 1
            for node in self.topology:
                input_interface = node.input_interface
                current_flow = node.flow
                output_interface = node.output_interface

                output_message, output_data = self._call_flow_from_state(
                    goal=node.goal,
                    input_interface=input_interface,
                    flow=current_flow,
                    output_interface=output_interface,
                )

                self._state_update_dict(update_data=output_data)

                # ~~~ Check for end of interaction
                if self._early_exit():
                    log.info(f"[{self.flow_config['name']}] End of interaction detected")
                    return

                if node.reset:
                    current_flow.reset(full_reset=True, recursive=True, src_flow=self)

        self._on_reach_max_rounds()
