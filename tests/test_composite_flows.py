import copy

import pytest
from src.flows import CompositeFlow, AtomicFlow


def atomic_flow_builder():
    class MyFlow(AtomicFlow):
        def run(self, input_data, expected_outputs):
            if self.dry_run:
                answer = 0
            else:
                answer = 0
                for k, v in input_data.items():
                    answer += v

            return {self.expected_outputs[0]: answer}

    return MyFlow(
        name="my-flow",
        description="flow-sum",
        expected_outputs=["sum"],
        expected_inputs=["v0", "v1"]
    )


def test_basic_instantiating() -> None:
    with pytest.raises(KeyError):
        CompositeFlow()

    flow_a = atomic_flow_builder()
    flow_b = atomic_flow_builder()

    flow = CompositeFlow(
        name="name",
        description="description",
        expected_inputs=["v0", "v1"],
        verbose=False,
        dry_run=True,
        flows={"flow_a": flow_a, "flow_b": flow_b}
    )

    assert not flow.verbose
    assert flow.dry_run
    assert len(flow.flow_config["flows"]) == 2
    assert isinstance(flow.flow_config["flows"]["flow_a"], AtomicFlow)
    assert isinstance(flow.flow_config["flows"]["flow_b"], AtomicFlow)


def test_basic_call() -> None:
    flow_a = atomic_flow_builder()
    flow_b = atomic_flow_builder()

    flow = CompositeFlow(
        name="name",
        description="description",
        expected_inputs=[],
        verbose=False,
        dry_run=True,
        flows={"flow_a": flow_a, "flow_b": flow_b}
    )

    flow.flow_state["v0"] = 12
    flow.flow_state["v1"] = 23

    answer = flow._call_flow_from_state(
        flow=flow.flow_config["flows"]["flow_a"],
        expected_outputs=["sum"]
    )

    assert answer.data["sum"] == 35
    assert len(flow.flow_state["history"]) == 2


if __name__ == "__main__":
    test_basic_call()
