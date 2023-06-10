import pytest
from flows.base_flows import FixedReplyAtomicFlow


def test_basic_instantiating() -> None:
    with pytest.raises(KeyError):
        FixedReplyAtomicFlow()

    with pytest.raises(KeyError):
        FixedReplyAtomicFlow(name="name", description="description")

    flow = FixedReplyAtomicFlow(
        name="name",
        description="description",
        expected_inputs=[],
        verbose=False,
        dry_run=True,
        fixed_reply="reply"
    )

    assert not flow.verbose
    assert flow.dry_run
    assert flow.fixed_reply == "reply"

    flow.fixed_reply = "new_reply"

    cfg = flow.flow_config
    state = flow.__getstate__()

    new_flow = FixedReplyAtomicFlow.load_from_config(cfg)

    assert not new_flow.verbose
    assert new_flow.dry_run
    assert new_flow.fixed_reply == "reply"

    new_flow_s = FixedReplyAtomicFlow.load_from_state(state)

    assert not new_flow_s.verbose
    assert new_flow_s.dry_run
    assert new_flow_s.fixed_reply == "new_reply"


def test_basic_call() -> None:
    flow = FixedReplyAtomicFlow(
        name="name",
        description="description",
        expected_inputs=[],
        verbose=False,
        dry_run=False,
        fixed_reply="reply"
    )

    tm = flow.package_task_message(
        recipient_flow=flow,
        task_name="",
        task_data={},
        expected_outputs=["query_mod"]
    )

    answer = flow(tm)
    assert "query" not in answer.data
    assert answer.data["query_mod"] == "reply"
    assert len(flow.flow_state["history"]) == 1


if __name__ == "__main__":
    test_basic_call()