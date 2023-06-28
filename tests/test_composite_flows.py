import copy

import pytest
from flows.base_flows import CompositeFlow, AtomicFlow


def atomic_flow_builder(dry_run=False):
    class MyFlow(AtomicFlow):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
        def run(self, input_data, output_keys):
            if self.dry_run:
                raise SystemExit(0)
            else:
                answer = 0
                for k, v in input_data.items():
                    answer += v

            return {self.output_keys[0]: answer}

    return MyFlow(
        name="my-flow",
        description="flow-sum",
        output_keys=["sum"],
        input_keys=["v0", "v1"],
        dry_run=dry_run
    )


def test_basic_instantiating() -> None:
    with pytest.raises(KeyError):
        CompositeFlow()

    flow_a = atomic_flow_builder()
    flow_b = atomic_flow_builder()

    flow = CompositeFlow(
        name="name",
        description="description",
        input_keys=["v0", "v1"],
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
        input_keys=[],
        verbose=False,
        dry_run=True,
        flows={"flow_a": flow_a, "flow_b": flow_b}
    )

    flow.flow_state["v0"] = 12
    flow.flow_state["v1"] = 23

    answer = flow._call_flow_from_state(
        flow=flow.flow_config["flows"]["flow_a"],
        output_keys=["sum"]
    )

    assert answer.data["sum"] == 35
    assert len(flow.flow_state["history"]) == 2

def test_dry_run():
    flow_a = atomic_flow_builder(dry_run=True)
    flow_b = atomic_flow_builder()

    flow = CompositeFlow(
        name="name",
        description="description",
        input_keys=[],
        verbose=False,
        dry_run=True,
        flows={"flow_a": flow_a, "flow_b": flow_b}
    )

    flow.flow_state["v0"] = 12
    flow.flow_state["v1"] = 23



    # ToDo: what is the expected behaviour for dry_run?
    # should we add SystemExit exceptions back to the call()?
    with pytest.raises(SystemExit):
        _ = flow._call_flow_from_state(
            flow=flow.flow_config["flows"]["flow_a"],
            output_keys=["sum"]
        )