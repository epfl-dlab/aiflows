from typing import List, Dict, Any

from flows.base_flows import CompositeFlow
from flows import utils

log = utils.get_pylogger(__name__)


class GeneratorCriticFlow(CompositeFlow):
    max_rounds: int
    init_generator_every_round: bool
    init_critic_every_round: bool

    def __init__(self, **kwargs):
        if "max_round" not in kwargs:
            kwargs["max_rounds"] = 2

        if "init_generator_every_round" not in kwargs:
            kwargs["init_generator_every_round"] = False

        if "init_critic_every_round" not in kwargs:
            kwargs["init_critic_every_round"] = False

        # ~~~ Creating the flow_config in super() ~~~
        super().__init__(**kwargs)

        flows = self.flow_config["flows"]
        assert len(flows) == 2, f"Generator Critic needs exactly two sub-flows, currently has {len(flows)}"

        # ~~~ check that we can identify flows ~~~
        self._identify_flows()

    def _identify_flows(self):
        generator, critic = None, None
        for flow_name, flow in self.flow_config["flows"].items():
            if "generator" in flow_name:
                generator = flow
            elif "critic" in flow_name:
                critic = flow
            else:
                error_message = f"{self.__class__.__name__} needs one flow with `critic` in its name" \
                                f"and one flow with `generator` in its name. Currently, the flow names are:" \
                                f"{self.flow_state['flows'].keys()}"

                raise Exception(error_message)
        return generator, critic

    def run(self, input_data: Dict[str, Any], expected_outputs: List[str]) -> Dict[str, Any]:
        generator_flow, critic_flow = self._identify_flows()

        # ~~~ sets the input_data in the class namespace ~~~
        self._update_state(update_data=input_data)

        for idx in range(self.max_rounds):
            # ~~~ Initialize the generator flow if needed ~~~
            if self.init_generator_every_round or idx == 0:
                generator_flow = self._init_flow(generator_flow)

            # ~~~ Execute the generator flow and update state with answer ~~~
            generator_answer = self._call_flow_from_state(
                flow=generator_flow
            )
            self._update_state(generator_answer)

            # ~~~ Check for end of interaction (decided by generator) ~~~
            if self._early_exit():
                log.info("End of interaction detected")
                break

            # ~~~ Initialize the critic flow ~~~
            if self.init_critic_every_round or idx == 0:
                critic_flow = self._init_flow(critic_flow)

            # ~~~ Execute the critic flow and update state with answer ~~~
            critic_answer = self._call_flow_from_state(
                flow=critic_flow
            )
            self._update_state(critic_answer)

        # ~~~ The final answer should be in self.flow_state, thus allow_class_namespace=False ~~~
        return self._get_keys_from_state(keys=expected_outputs, allow_class_namespace=False)
