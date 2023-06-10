import pytest

from src.flows import SequentialFlow, AtomicFlow


def atomic_flow_builder(bias):
    class MyFlow(AtomicFlow):
        def run(self, input_data, expected_outputs):
            answer = self.flow_config["bias"]
            for k, v in input_data.items():
                answer += v
            return {self.expected_outputs[0]: answer}

    return MyFlow(
        name="my-flow",
        description="flow-sum",
        expected_outputs=["v0"],
        expected_inputs=["v0"],
        bias=bias
    )


def test_basic_instantiating() -> None:
    with pytest.raises(KeyError):
        SequentialFlow()

    with pytest.raises(Exception):
        SequentialFlow(name="name", description="description")

    flow_a = atomic_flow_builder(10)
    flow_b = atomic_flow_builder(1)

    flow = SequentialFlow(
        name="name",
        description="description",
        expected_inputs=["v0"],
        verbose=False,
        dry_run=True,
        flows={"flow_a": flow_a, "flow_b": flow_b}
    )

    assert not flow.verbose
    assert flow.dry_run
    assert len(flow.flow_config["flows"]) == 2
    assert isinstance(flow.flow_config["flows"]["flow_a"], AtomicFlow)
    assert isinstance(flow.flow_config["flows"]["flow_b"], AtomicFlow)


def test_basic_call():
    flow_a = atomic_flow_builder(bias=2)
    flow_b = atomic_flow_builder(bias=4)

    seq_flow = SequentialFlow(
        name="name",
        description="description",
        expected_inputs=["v0"],
        expected_outputs=["v0"],
        dry_run=False,
        max_rounds=3,
        eoi_key=None,
        max_round=2,
        flows={"generator": flow_a, "critic": flow_b}
    )

    data = {"v0": 10}
    task_message = seq_flow.package_task_message(
        recipient_flow=seq_flow,
        task_name="task",
        task_data=data,
        expected_outputs=["v0"]
    )

    answer = seq_flow(task_message)
    assert answer.data["v0"] == 16


if __name__ == "__main__":
    test_basic_call()
