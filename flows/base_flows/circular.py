import copy
from typing import List, Dict, Any, Optional

from flows.base_flows import CompositeFlow, Flow
from flows.data_transformations.abstract import DataTransformation

from flows.utils.general_helpers import validate_parameters
from ..utils import logging

log = logging.get_logger(__name__)

class TopologyNode:
    def __init__(self, 
                 flow: Flow, 
                 reset_every_round: bool,
                 output_transformations: List[DataTransformation]) -> None:
        super().__init__()
        self.flow = flow
        self.reset_every_round = reset_every_round
        self.output_transformations = output_transformations


class CircularFlow(CompositeFlow):
    REQUIRED_KEYS_CONFIG = ["max_rounds", "early_exit_key", "topology"]
    REQUIRED_KEYS_CONSTRUCTOR = ["subflows", "subflows_dict"]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.topology = self.__set_up_topology()
        self._extend_keys_to_ignore_when_resetting_namespace(["topology"])
    
    def __set_up_topology(self) -> List[TopologyNode]:
        topology = self.flow_config.get("topology", [])
        ret = []
        if len(topology) == 0:
            raise ValueError(f"topology is empty for flow {self.flow_config['name']}")
        
        # parse topology
        for flow_name, topo_config in topology.items():
            if flow_name not in self.subflows_dict:
                raise ValueError(f"flow {flow_name} is not in subflow_configs")
            
            flow = self.subflows_dict[flow_name]
            reset_every_round = topo_config.get("reset_every_round", False)
            output_transformations = self._set_up_data_transformations(topo_config.get("output_transformations", []))

            ret.append(TopologyNode(flow=flow, 
                                    reset_every_round=reset_every_round,
                                    output_transformations=output_transformations))
        return ret

    @classmethod
    def _validate_parameters(cls, kwargs):
        validate_parameters(cls, kwargs)

        assert len(kwargs["subflows"]) > 0, f"Circular flow needs at least one flow, currently has 0"

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        # ~~~ sets the input_data in the flow_state dict ~~~
        self._state_update_dict(update_data=input_data)

        max_round = self.flow_config.get("max_rounds", 1)

        self._sequential_run(max_round=max_round)

        # ~~~ The final answer should be in self.flow_state, thus allow_class_attributes=False ~~~
        # print(f"output keys: {self.get_output_keys()}")
        outputs = self._fetch_state_attributes_by_keys(keys=self.get_output_keys(),
                                                       allow_class_attributes=False)
        return outputs

    @classmethod
    def type(cls):
        return "circular"
    
    def _on_reach_max_round(self):
        return

    def _sequential_run(self, max_round: int):
        # default value, though it should never be returned because max_round should be > 0
        for _ in range(max_round):
            for node in self.topology:
                current_flow = node.flow
                output_transformations = node.output_transformations
                if node.reset_every_round:
                    current_flow.reset(full_reset=True, recursive=True, src_flow=self)

                output_message = self._call_flow_from_state(
                    flow_to_call=current_flow)
                output_data = output_message.data["output_data"]

                # ~~~ Apply output transformations
                # import pdb
                # pdb.set_trace()
                for output_transformation in output_transformations:
                    output_data = output_transformation(output_data)

                self._state_update_dict(update_data=output_data)
                # ~~~ Check for end of interaction
                if self._early_exit():
                    log.info(f"[{self.flow_config['name']}] End of interaction detected")
                    return

        self._on_reach_max_round()
        log.info(f"[{self.flow_config['name']}] Max round reached. Returning output, answer might be incomplete.")

