import pytest
from flows.base_flows import CodeTestingAtomicFlowCodeforces

debugging_setup = {
    "compilation_error_template": "Compilation error",
    "timeout_error_template": "Timeout error",
    "runtime_error_template": "Runtime error",
    "single_test_error_template": "Single test error",
    "single_test_error_message": "Single test error message",
    "test_error_template": "Test error",
    "tests_separator": "Tests separator",
    "all_tests_header": "All tests header",
}


def test_basic_instantiating_cf() -> None:
    with pytest.raises(KeyError):
        CodeTestingAtomicFlowCodeforces()

    with pytest.raises(KeyError):
        CodeTestingAtomicFlowCodeforces(
            name="Codeforces Code Testing",
            description="Testing Codeforces Code",
            verbose=False,
            dry_run=True,
            flow_type="debug-atomic-flow"
        )

    flow = CodeTestingAtomicFlowCodeforces(
        name="Codeforces Code Testing",
        description="Testing Codeforces Code",
        debugging_setup=debugging_setup,
        verbose=False,
        dry_run=True,
        flow_type="debug-atomic-flow"
    )

    assert not flow.verbose
    assert flow.dry_run
    assert flow.flow_type == "debug-atomic-flow"


def test_instantiating_extra_params() -> None:
    flow = CodeTestingAtomicFlowCodeforces(
        name="Codeforces Code Testing",
        description="Testing Codeforces Code",
        debugging_setup=debugging_setup,
        verbose=False,
        dry_run=True,
        flow_type="debug-atomic-flow",
        new_arg="new_arg_val"
    )

    assert flow.new_arg == "new_arg_val"

    cfg = flow.flow_config
    new_flow = CodeTestingAtomicFlowCodeforces.load_from_config(cfg)
    assert new_flow.new_arg == "new_arg_val"

    state = flow.__getstate__()
    new_flow_from_state = CodeTestingAtomicFlowCodeforces.load_from_state(flow_state=state)
    assert new_flow_from_state.new_arg == "new_arg_val"


def test_cf_tool_basic():
    flow = CodeTestingAtomicFlowCodeforces(
        name="Codeforces Code Testing",
        description="Testing Codeforces Code",
        debugging_setup=debugging_setup,
        verbose=False,
        dry_run=True,
        flow_type="debug-atomic-flow"
    )

    input_data = {
        "code": "n=int(input())\nprint(n)",
        "public_tests_individual_io": [[["1"], "1"]]
    }

    task_message = flow.package_task_message(
        recipient_flow=flow,
        task_name="",
        task_data=input_data,
        expected_outputs=[]
    )

    answer = flow(task_message)
    assert answer.data["all_tests_passed"]
    assert not answer.data["compilation_error_message"]
    assert answer.data["compilation_status"]
    assert answer.data["public_tests_results"][0]["status"]
    assert not answer.data["timeout_error"]

# if __name__ == "__main__":
#     test_basic_instantiating_cf()
#     test_instantiating_extra_params()
#     test_cf_tool_basic()
