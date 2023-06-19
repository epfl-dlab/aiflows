from typing import List, Dict, Any

from flows.base_flows import CompositeFlow
from flows import utils

log = utils.get_pylogger(__name__)


class GeneratorCriticFlow(CompositeFlow):
    def __init__(self, **kwargs):
        self._validate_parameters(kwargs)
        super().__init__(**kwargs)

    @classmethod
    def _validate_parameters(cls, kwargs):
        # ToDo: Deal with this in a cleaner way (with less repetition)
        super()._validate_parameters(kwargs)

        if "max_rounds" not in kwargs["flow_config"]:
            raise KeyError("Generator Critic needs a `max_rounds` parameter")

        if "reset_generator_every_round" not in kwargs["flow_config"]:
            raise KeyError("Generator Critic needs a `reset_generator_every_round` parameter")

        if "reset_critic_every_round" not in kwargs["flow_config"]:
            raise KeyError("Generator Critic needs a `reset_critic_every_round` parameter")

        if "early_exit_key" not in kwargs["flow_config"]:
            raise KeyError("Generator Critic needs a `early_exit_key` parameter")

        if "subflows" not in kwargs:
            raise KeyError("Generator Critic needs a `subflows` parameter")

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

    def run(self, input_data: Dict[str, Any], expected_outputs: List[str]) -> Dict[str, Any]:
        generator_flow, critic_flow = self._identify_flows()

        # ~~~ sets the input_data in the flow_state dict ~~~
        self._update_state(update_data=input_data)

        for idx in range(self.flow_config["max_rounds"]):
            # ~~~ Initialize the generator flow if needed ~~~
            if self.flow_config["reset_generator_every_round"] or idx == 0:
                if isinstance(generator_flow, CompositeFlow):
                    generator_flow.reset(full_reset=True, recursive=True)
                else:
                    generator_flow.reset(full_reset=True)

            # ~~~ Execute the generator flow and update state with answer ~~~
            generator_answer = self._call_flow_from_state(
                flow=generator_flow
            )
            self._update_state(generator_answer)

            # ~~~ Check for end of interaction (decided by generator) ~~~
            if self._early_exit():
                log.info(f"[{self.flow_config['name']}] End of interaction detected")
                break

            # ~~~ Initialize the critic flow ~~~
            if self.flow_config["reset_critic_every_round"] or idx == 0:
                if isinstance(critic_flow, CompositeFlow):
                    critic_flow.reset(full_reset=True, recursive=True)
                else:
                    critic_flow.reset(full_reset=True)

            # ~~~ Execute the critic flow and update state with answer ~~~
            critic_answer = self._call_flow_from_state(
                flow=critic_flow
            )
            self._update_state(critic_answer)

        # ~~~ The final answer should be in self.flow_state, thus allow_class_namespace=False ~~~
        return self._get_keys_from_state(keys=expected_outputs, allow_class_namespace=False)
