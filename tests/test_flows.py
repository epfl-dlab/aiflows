import pytest

from src.flows.abstract import Flow
from src.flows.code_testing_atomic import CodeTestingAtomicFlowCodeforces
from src.messages import InputMessage, FlowMessage


def test_abstract_flow():
    flow = Flow("Abstract Flow", "Abstract Flow", [], [])

    # not implemented
    with pytest.raises(NotImplementedError):
        flow._flow()


def test_code_testing_codeforces():
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

    flow = CodeTestingAtomicFlowCodeforces("Codeforces Code Testing", "Codeforces Code Testing", [], [],
                                           debugging_setup)

    inp = InputMessage(
        inputs={
            "code":
                FlowMessage(
                    flow_run_id=flow.flow_run_id,
                    flow_runner=flow.name,
                    message_creator=flow.name,
                    content="n=int(input())\nprint(n)",
                    parents=[]
                ),
            "public_tests_individual_io": FlowMessage(
                flow_run_id=flow.flow_run_id,
                flow_runner=flow.name,
                message_creator=flow.name,
                content=[[["1"], "1"]],
                parents=[]
            )
        },
        message_creator=flow.name,
        flow_run_id=flow.flow_run_id,
        flow_runner=flow.name,
        content="input message",
        target_flow=flow.flow_run_id,
        parents=[]
    )
    flow.run(inp)
