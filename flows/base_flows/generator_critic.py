from typing import List, Dict, Any, Optional

from flows.base_flows import CircularFlow
from ..utils import logging
from flows.utils.general_helpers import validate_parameters

log = logging.get_logger(__name__)

# ToDo(https://github.com/epfl-dlab/flows/issues/62): Add a flag controlling whether to skip the critic in the last round


class GeneratorCriticFlow(CircularFlow):
    REQUIRED_KEYS_CONFIG = ["max_rounds", "early_exit_key"]
    # REQUIRED_KEYS_CONSTRUCTOR = ["subflows"]

    def __init__(self, **kwargs):
        kwargs.get("flow_config", {}).update({"reset_every_round": {flow_name: True for flow_name in kwargs["subflows"].keys()}})
        super().__init__(**kwargs)

    @classmethod
    def _validate_parameters(cls, kwargs):
        validate_parameters(cls, kwargs)

        for flow_name, flow in kwargs["subflows"].items():
            if "generator" in flow_name.lower():
                continue
            elif "critic" in flow_name.lower():
                continue
            else:
                error_message = f"{cls.__class__.__name__} needs one flow with `critic` in its name" \
                                f"and one flow with `generator` in its name. Currently, the flow names are:" \
                                f"{kwargs['subflows'].keys()}"

                raise Exception(error_message)

    # def _identify_flows(self):
    #     generator, critic = None, None
    #
    #     for flow_name, flow in self.subflows.items():
    #         if "generator" in flow_name.lower():
    #             generator = flow
    #         elif "critic" in flow_name.lower():
    #             critic = flow
    #
    #     return generator, critic

    def run(self,
            input_data: Dict[str, Any],
            private_keys: Optional[List[str]] = [],
            keys_to_ignore_for_hash: Optional[List[str]] = []) -> Dict[str, Any]:

        # GeneratorCriticFlow requires the Generator and Critic to reset every round
        self.flow_config["reset_every_round"] = {flow_name: True for flow_name in self.subflows.keys()}

        return super().run(input_data=input_data, private_keys=private_keys, keys_to_ignore_for_hash=keys_to_ignore_for_hash)


    @classmethod
    def type(cls):
        return "GeneratorCriticFlow"
