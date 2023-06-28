import pdb
from typing import List, Dict, Any, Optional

from flows.base_flows import CompositeFlow
from flows import utils
from flows.utils.general_helpers import validate_parameters

log = utils.get_pylogger(__name__)


class GeneratorCriticFlow(CompositeFlow):
    REQUIRED_KEYS_CONFIG = ["max_rounds", "reset_generator_every_round", "reset_critic_every_round", "early_exit_key"]
    REQUIRED_KEYS_KWARGS = ["subflows"]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.api_keys = None

    @classmethod
    def _validate_parameters(cls, kwargs):
        validate_parameters(cls, kwargs)

        for flow_name, flow in kwargs["subflows"].items():
            if "generator" in flow_name.lower():
                pass
            elif "critic" in flow_name.lower():
                pass
            else:
                error_message = f"{cls.__class__.__name__} needs one flow with `critic` in its name" \
                                f"and one flow with `generator` in its name. Currently, the flow names are:" \
                                f"{kwargs['subflows'].keys()}"

                raise Exception(error_message)

    def _identify_flows(self):
        generator, critic = None, None

        for flow_name, flow in self.subflows.items():
            if "generator" in flow_name.lower():
                generator = flow
            elif "critic" in flow_name.lower():
                critic = flow

        return generator, critic

    def run(self,
            input_data: Dict[str, Any],
            private_keys: Optional[List[str]] = [],
            keys_to_ignore_for_hash: Optional[List[str]] = []) -> Dict[str, Any]:
        self.flow_state["api_keys"] = input_data["api_keys"]
        del input_data["api_keys"]

        generator_flow, critic_flow = self._identify_flows()

        # ~~~ sets the input_data in the flow_state dict ~~~
        self._state_update_dict(update_data=input_data)

        for idx in range(self.flow_config["max_rounds"]):
            # ~~~ Initialize the generator flow if needed ~~~
            if self.flow_config["reset_generator_every_round"]:
                generator_flow.reset(full_reset=True, recursive=True)


            # ~~~ Execute the generator flow and update the state with the outputs ~~~
            generator_output_message = self._call_flow_from_state(
                flow_to_call=generator_flow,
                private_keys=private_keys,
                keys_to_ignore_for_hash=keys_to_ignore_for_hash
            )
            self._state_update_dict(generator_output_message)


            # ~~~ Check for end of interaction (decided by the generator) ~~~
            if self._early_exit():
                log.info(f"[{self.flow_config['name']}] End of interaction detected")
                break


            # ~~~ Initialize the critic flow ~~~
            if self.flow_config["reset_critic_every_round"]:
                critic_flow.reset(full_reset=True, recursive=True)

            # ~~~ Execute the critic flow and update the state with the outputs ~~~
            # ToDo This is where the critic flow should be called and yields error
            critic_output_message = self._call_flow_from_state(
                flow_to_call=critic_flow,
                private_keys=private_keys,
                keys_to_ignore_for_hash=keys_to_ignore_for_hash
            )

            self._state_update_dict(critic_output_message)

        # ~~~ The final answer should be in self.flow_state, thus allow_class_attributes=False ~~~
        outputs = self._fetch_state_attributes_by_keys(keys=input_data["output_keys"],
                                                       allow_class_attributes=False)
        return outputs
