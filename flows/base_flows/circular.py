from typing import List, Dict, Any, Union

import hydra

import flows.interfaces
from flows.base_flows import CompositeFlow, Flow
from flows.data_transformations.abstract import DataTransformation

from ..utils import logging

log = logging.get_logger(__name__)


class TopologyNode:
    def __init__(self,
                 goal,
                 input_interface,
                 flow: Flow,
                 output_interface: List[DataTransformation],
                 reset: bool) -> None:
        self.goal = goal
        self.input_interface = input_interface
        self.flow = flow
        self.output_interface = output_interface
        self.reset = reset


class CircularFlow(CompositeFlow):
    REQUIRED_KEYS_CONFIG = ["max_rounds", "early_exit_key", "topology"]

    __default_flow_config = {
        "max_rounds": 3,
        "early_exit_key": "EARLY_EXIT",
        "topology": []
    }

    __input_msg_payload_builder_registry = {}
    __output_msg_payload_processor_registry = {}

    @staticmethod
    def input_msg_payload_builder(builder_fn):
        def wrapper(goal, data_dict, src_flow: Flow, dst_flow: Flow):
            return builder_fn(src_flow, data_dict, dst_flow)

        CircularFlow.__input_msg_payload_builder_registry[builder_fn.__qualname__] = wrapper
        log.debug(f"input_msg_payload_builder [{builder_fn.__qualname__}] registered")
        return wrapper

    @staticmethod
    def output_msg_payload_processor(processor_fn):
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
        super().__init__(flow_config=flow_config,
                         subflows=subflows)
        if len(self.subflows) <= 0:
            raise ValueError(f"Circular flow needs at least one subflow, currently has 0")
        self.topology = self.__set_up_topology()

    def _early_exit(self):
        early_exit_key = self.flow_config.get("early_exit_key", None)
        if early_exit_key:
            if early_exit_key in self.flow_state:
                return bool(self.flow_state[early_exit_key])
            elif early_exit_key in self.__dict__:
                return bool(self.__dict__[early_exit_key])

        return False

    def __set_up_topology(self) -> List[TopologyNode]:
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
                input_interface = flows.interfaces.KeyInterface()
                input_interface.transformations.append(flows.data_transformations.KeyMatchInput())

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

            ret.append(TopologyNode(goal=topo_config["goal"],
                                    input_interface=input_interface,
                                    flow=flow,
                                    output_interface=output_interface,
                                    reset=reset))

        return ret

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        # ~~~ sets the input_data in the flow_state dict ~~~
        self._state_update_dict(update_data=input_data)

        max_rounds = self.flow_config.get("max_rounds", 1)
        if max_rounds is None:
            log.info(f"Running {self.flow_config['name']} without `max_rounds` until the early exit condition is met.")

        self._sequential_run(max_rounds=max_rounds)

        output = self._get_output_from_state()

        return output

    def _get_output_from_state(self):
        outputs = self._fetch_state_attributes_by_keys(keys=self.get_interface_description()["output"])
        return outputs

    @classmethod
    def type(cls):
        return "circular"

    def _on_reach_max_rounds(self):
        log.info(f"[{self.flow_config['name']}] Max rounds reached. Returning output, answer might be incomplete.")
        return

    def _sequential_run(self, max_rounds: Union[int, None]):
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
                    output_interface=output_interface)

                self._state_update_dict(update_data=output_data)

                # ~~~ Check for end of interaction
                if self._early_exit():
                    log.info(f"[{self.flow_config['name']}] End of interaction detected")
                    return

                if node.reset:
                    current_flow.reset(full_reset=True, recursive=True, src_flow=self)

        self._on_reach_max_rounds()
