import pytest

from flows.base_flows import AtomicFlow, GeneratorCriticFlow, FixedReplyFlow


def atomic_flow_builder():
    class MyFlow(AtomicFlow):
        def input_keys_given_state(self):
            if self.is_conv_init():
                return ["query"]
            else:
                return self.input_keys

        def is_conv_init(self):
            conv_init = False
            if "conversation_initialized" in self.flow_state:
                conv_init = self.flow_state["conversation_initialized"]

            return conv_init

        def run(self, input_data, output_keys):
            if not self.is_conv_init():
                answer = 0
                self.flow_state["conversation_initialized"] = True
            else:
                answer = self.flow_state["prev_answer"]

            for k, v in input_data.items():
                answer += v
            self.flow_state["prev_answer"] = answer
            return {self.output_keys[0]: answer}

    return MyFlow(name="my-flow", description="flow-sum", output_keys=["sum"], input_keys=["v0", "v1"])


def test_basic_instantiating() -> None:
    with pytest.raises(KeyError):
        GeneratorCriticFlow()

    with pytest.raises(KeyError):
        GeneratorCriticFlow(name="name", description="description")

    flow_a = atomic_flow_builder()
    flow_b = FixedReplyFlow(
        name="name", description="description", input_keys=[], verbose=False, dry_run=False, fixed_reply="reply"
    )

    with pytest.raises(Exception):
        GeneratorCriticFlow(
            name="name",
            description="description",
            input_keys=["v0", "v1"],
            verbose=False,
            dry_run=False,
            flows={"gen": flow_a, "critic": flow_b},
        )

    with pytest.raises(Exception):
        GeneratorCriticFlow(
            name="name",
            description="description",
            input_keys=["v0", "v1"],
            verbose=False,
            dry_run=False,
            flows={"generator": flow_a, "cri": flow_b},
        )

    flow = GeneratorCriticFlow(
        name="name",
        description="description",
        input_keys=["v0", "v1"],
        verbose=False,
        dry_run=False,
        flows={"generator": flow_a, "critic": flow_b},
    )

    assert not flow.verbose
    assert not flow.dry_run
    assert len(flow.flow_config["flows"]) == 2
    assert isinstance(flow.flow_config["flows"]["generator"], AtomicFlow)
    assert isinstance(flow.flow_config["flows"]["critic"], FixedReplyFlow)


def test_basic_call():
    flow_a = atomic_flow_builder()

    flow_b = FixedReplyFlow(
        name="name", description="description", input_keys=[], output_keys=["query"], fixed_reply=10
    )

    gen_crit_flow = GeneratorCriticFlow(
        name="name",
        description="description",
        input_keys=["v0", "v1"],
        output_keys=["sum"],
        dry_run=False,
        max_rounds=3,
        eoi_key=None,
        max_round=2,
        flows={"generator": flow_a, "critic": flow_b},
    )

    data = {"v0": 12, "v1": 23}
    task_message = gen_crit_flow.package_task_message(
        recipient_flow=gen_crit_flow, task_name="task", task_data=data, output_keys=["sum"]
    )

    answer = gen_crit_flow(task_message)
    assert answer.data["sum"] == 55
