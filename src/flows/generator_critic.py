from typing import List, Dict

from src.flows import CompositeFlow, Flow
from src.messages import TaskMessage
from src import utils

log = utils.get_pylogger(__name__)


class GeneratorCriticFlow(CompositeFlow):
    def __init__(
            self,
            name: str,
            description: str,
            expected_inputs: List[str],
            expected_outputs: List[str],
            flows: Dict[str, Flow],
            n_rounds: int,
            init_generator_every_round: bool = False,
            init_critic_every_round: bool = True,
            eoi_key: str = None,
            verbose: bool = False
    ):
        super().__init__(
            name=name,
            description=description,
            expected_inputs=expected_inputs,
            expected_outputs=expected_outputs,
            flows=flows,
            verbose=verbose
        )

        self.n_rounds = n_rounds

        assert len(flows) == 2, f"Generator Critic needs exactly two sub-flows, currently has {len(flows)}"

        self._identify_flows()

        self.expected_generator_output_keys = self.flows[self.generator_name].expected_outputs

        self.init_generator_every_round = init_generator_every_round
        self.init_critic_every_round = init_critic_every_round

        if eoi_key:
            self.eoi_key = eoi_key
        else:
            self._set_eoi_key()

    def _identify_flows(self):
        for flow_name, flow in self.flows.items():
            if "generator" in flow_name:
                self.generator_name = flow_name
            elif "critic" in flow_name:
                self.critic_name = flow_name
            else:
                raise Exception("Generator Critic flow needs one flow with `critic` in its name "
                                "and one flow with `generator` in its name")

    def _set_eoi_key(self):
        generator_flow = self.flows[self.generator_name]
        if hasattr(generator_flow, "end_of_interaction_key") and callable(generator_flow.end_of_interaction_key):
            eoi_key = generator_flow.end_of_interaction_key()
            assert eoi_key in self.expected_generator_output_keys, \
                f"The end of interaction key from {eoi_key} is not part of its expected outputs"
            self.eoi_key = eoi_key

    def _is_eoi(self):
        if self.eoi_key in self.state:
            return bool(self.state[self.eoi_key].content)
        return False

    def run(self, task_message: TaskMessage):
        # ~~~ Initialize flows ~~~
        generator_flow = self.flows[self.generator_name]
        critic_flow = self.flows[self.critic_name]
        generator_flow.initialize()
        critic_flow.initialize()

        # ~~~ Propagate API-keys ~~~
        api_key = self.state["api_key"]
        generator_flow.set_api_key(api_key=api_key)
        critic_flow.set_api_key(api_key=api_key)

        # ~~~ Prepare information to send to flows ~~~
        _generator_call_inputs = task_message.data
        _parent_message_ids = [task_message.message_id]

        for idx in range(self.n_rounds):
            # ~~~ Initialize the generator flow if needed ~~~
            if self.init_generator_every_round and idx > 0:
                generator_flow.initialize()


            # ~~~ Execute the generator flow and update state ~~~
            generator_answer = self._call_flow(
                flow_id=self.generator_name,
                parent_message_ids=_parent_message_ids,
            )
            self._update_state(generator_answer)

            # ~~~ Check for end of interaction decided by generator ~~~
            if self._is_eoi():
                log.info("End of interaction detected")
                break

            # ~~~ Initialize the critic flow ~~~
            if self.init_critic_every_round and idx > 0:
                critic_flow.initialize()
                critic_flow.set_api_key(api_key=api_key)

            # ~~~ Execute the critic flow and update state ~~~
            critic_answer = self._call_flow(
                flow_id=self.critic_name,
                parent_message_ids=[generator_answer.message_id]
            )
            self._update_state(critic_answer)
            _parents = [critic_answer.message_id]

