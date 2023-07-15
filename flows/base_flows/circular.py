from typing import List, Dict, Any, Optional

from flows.base_flows import CompositeFlow
from flows.utils.general_helpers import validate_parameters
from ..utils import logging

log = logging.get_logger(__name__)



class CircularFlow(CompositeFlow):
    REQUIRED_KEYS_CONFIG = ["max_rounds", "reset_every_round", "early_exit_key"]
    REQUIRED_KEYS_CONSTRUCTOR = ["subflows"]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @classmethod
    def _validate_parameters(cls, kwargs):
        validate_parameters(cls, kwargs)

        assert len(kwargs["subflows"]) > 0, f"Circular flow needs at least one flow, currently has 0"

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        # ~~~ sets the input_data in the flow_state dict ~~~
        self._state_update_dict(update_data=input_data)

        max_round = self.flow_config.get("max_rounds", 1)

        output_message = self._sequential_run(max_round=max_round)

        # ~~~ The final answer should be in self.flow_state, thus allow_class_attributes=False ~~~
        outputs = self._fetch_state_attributes_by_keys(keys=output_message.data["output_keys"],
                                                       allow_class_attributes=False)

        return outputs

    @classmethod
    def type(cls):
        return "circular"

    def _sequential_run(self, max_round:int) -> Dict[str, Any]:
        # default value, though it should never be returned because max_round should be > 0
        output_message = {}
        for idx in range(max_round):
            for flow_name, current_flow in self.subflows.items():
                current_flow.reset(src_flow=self, **self.flow_config["reset_every_round"].get(flow_name))

                output_message = self._call_flow_from_state(
                    flow_to_call=current_flow)
                self._state_update_dict(update_data=output_message)

                # ~~~ Check for end of interaction
                if self._early_exit():
                    log.info(f"[{self.flow_config['name']}] End of interaction detected")
                    return output_message
        log.info(f"[{self.flow_config['name']}] Max round reached. Returning output, answer might be incomplete.")
        return output_message

