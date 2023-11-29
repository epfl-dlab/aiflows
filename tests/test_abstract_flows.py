import pytest

from flows.base_flows.abstract import Flow
from flows.history import FlowHistory


def test_basic_instantiating() -> None:
    with pytest.raises(KeyError):
        Flow()

    Flow(name="name", description="description")

    flow = Flow(name="name", description="description", input_keys=[], verbose=False, dry_run=True, flow_type="my-flow")

    assert not flow.verbose
    assert flow.dry_run
    assert flow.flow_type == "my-flow"

    with pytest.raises(NotImplementedError):
        flow.run(input_data={}, output_keys=[])


def test_instantiating_extra_params() -> None:
    flow = Flow(
        name="name",
        description="description",
        input_keys=[],
        verbose=False,
        dry_run=True,
        flow_type="my-flow",
        new_arg="new_arg_val",
    )

    assert flow.new_arg == "new_arg_val"

    cfg = flow.flow_config
    new_flow = Flow.load_from_config(cfg)
    assert new_flow.new_arg == "new_arg_val"

    state = flow.__getstate__()
    new_flow_from_state = Flow.load_from_state(flow_state=state)
    assert new_flow_from_state.new_arg == "new_arg_val"


def test_cfg_loading() -> None:
    fc = {"name": "name", "description": "description", "flow_type": "my-flow"}

    flow = Flow.load_from_config(fc)
    assert flow.name == "name"
    assert flow.description == "description"
    assert flow.flow_type == "my-flow"

    new_fc = flow.flow_config
    new_flow = Flow.load_from_config(new_fc)
    assert new_flow.name == "name"
    assert new_flow.description == "description"
    assert new_flow.flow_type == "my-flow"

    assert flow.flow_run_id != new_flow.flow_run_id
    assert flow.flow_state["history"] != new_flow.flow_state["history"]

    flow._update_state({"data": [2, 3]})
    flow._update_state({"name": "new-name"})

    new_fc = flow.flow_config
    different_flow = Flow.load_from_config(new_fc)
    assert different_flow.name == "name"
    assert different_flow.flow_run_id != flow.flow_run_id


def test_state_loading() -> None:
    # ~~~ Test without flow_state ~~~
    f = Flow(name="name", description="description")

    state = f.__getstate__()
    f.name = "modified"
    restarted_f = Flow.load_from_state(state)

    assert restarted_f.name == "name"

    # ~~~ Test with flow_state ~~~
    flow = Flow(name="name", description="description", input_keys=[], verbose=False, dry_run=True, flow_type="my-flow")

    flow.flow_state["data"] = "example_data"
    flow.not_to_be_saved = "temp"

    flow_full_state = flow.__getstate__()

    flow.name = "modified_name"
    flow.flow_state["data"] = "modified_data"

    restarted_flow = Flow.load_from_state(flow_full_state)

    assert restarted_flow.name == "name"
    assert restarted_flow.flow_state["data"] == "example_data"
    assert not hasattr(restarted_flow, "not_to_be_saved")
    assert restarted_flow.flow_run_id != flow.flow_run_id


def test_update_state() -> None:
    f = Flow(name="name", description="description")

    assert hasattr(f, "flow_state")
    assert type(f.flow_state) == dict
    assert "history" in f.flow_state
    assert type(f.flow_state["history"]) == FlowHistory

    f.flow_state["data"] = "data_0"
    assert len(f.flow_state["history"]) == 0

    f._update_state(update_data={"data": "modified", "new": "value"})
    assert f.flow_state["data"] == "modified"
    assert f.flow_state["new"] == "value"
    assert len(f.flow_state["history"]) == 1
    assert f.flow_state["history"].get_latest_message().updated_keys == ["data", "new"]

    # ~~~ Should have no effect on data ~~~
    f._update_state(update_data={"data": None, "param": 4})
    assert f.flow_state["data"] == "modified"
    assert f.flow_state["param"] == 4
    assert f.flow_state["new"] == "value"
    assert len(f.flow_state["history"]) == 2
    assert f.flow_state["history"].get_latest_message().updated_keys == ["param"]

    # ~~~ Should have no effect on data ~~~
    f._update_state(update_data={"data": None})
    assert f.flow_state["data"] == "modified"
    assert f.flow_state["param"] == 4
    assert f.flow_state["new"] == "value"
    assert len(f.flow_state["history"]) == 2
    assert f.flow_state["history"].get_latest_message().updated_keys == ["param"]


def test_basic_run() -> None:
    class MyFlow(Flow):
        def run(self, input_data, output_keys):
            self.temporary_variable = input_data["second_input"]
            self._update_state({"input_0": input_data["first_input"]})
            self.other_temp = 24 + len(self.flow_state["history"])

            return {output_keys[0]: self.temporary_variable, output_keys[1]: self.other_temp}

    flow = MyFlow(
        name="name",
        description="description",
        input_keys=["first_input", "second_input"],
        output_keys=["first_output", "second_output"],
        verbose=False,
        dry_run=True,
        flow_type="my-flow",
    )

    task_message = flow.package_task_message(
        recipient_flow=flow,
        task_name="task",
        task_data={"first_input": 23, "second_input": 87},
        output_keys=["first_output", "second_output"],
    )

    output_message = flow(task_message=task_message)

    assert output_message.data["first_output"] == 87
    assert output_message.data["second_output"] == 26
    assert not hasattr(flow, "temporary_variable")
    assert not hasattr(flow, "other_temp")
    assert flow.flow_state["input_0"] == 23
    assert len(flow.flow_state["history"]) == 2
    assert flow.flow_state["history"].get_latest_message().updated_keys == ["input_0"]

    output_message = flow(task_message=task_message)

    assert output_message.data["first_output"] == 87
    assert output_message.data["second_output"] == 27
    assert not hasattr(flow, "temporary_variable")
    assert not hasattr(flow, "other_temp")
    assert flow.flow_state["input_0"] == 23
    assert len(flow.flow_state["history"]) == 3
    # assert flow.flow_state["history"].get_latest_message().updated_keys == ["input_0"]

    new_task_message = flow.package_task_message(
        recipient_flow=flow,
        task_name="task",
        task_data={"first_input": 12, "second_input": 32},
        output_keys=["first_output", "second_output"],
    )

    output_message = flow(task_message=new_task_message)

    assert output_message.data["first_output"] == 32
    assert output_message.data["second_output"] == 29
    assert not hasattr(flow, "temporary_variable")
    assert not hasattr(flow, "other_temp")
    assert flow.flow_state["input_0"] == 12
    assert len(flow.flow_state["history"]) == 5
    assert flow.flow_state["history"].get_latest_message().updated_keys == ["input_0"]
