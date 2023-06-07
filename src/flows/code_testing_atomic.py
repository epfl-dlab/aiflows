import copy
from typing import List, Optional, Dict, Any

import jinja2

from src.flows import AtomicFlow
from src.message_annotators.abstract import MessageAnnotator
from src.messages import TaskMessage

import src.tools.code_evaluation.testing_utils_leetcode as testing_utils_leetcode
import src.tools.code_evaluation.testing_utils_codeforces as testing_utils_codeforces


class CodeTestingAtomicFlow(AtomicFlow):
    def __init__(
        self,
        name: str,
        description: str,
        expected_outputs: List[str],
        expected_inputs: List[str],
        debugging_setup: Dict,
        response_annotators: Optional[Dict[str, MessageAnnotator]] = None,
        verbose: bool = False
    ):

        super().__init__(
            name=name,
            description=description,
            expected_inputs=expected_inputs,
            expected_outputs=expected_outputs,
            verbose=verbose,
        )

        self.response_annotators = response_annotators if response_annotators else {}
        self.debugging_setup = debugging_setup
        self.special_output_key = "issue_description"

    def _get_tests_io(self, task_message: TaskMessage):
        # If tests were not provided this function could be used to generate some based on the problem description
        return task_message.data["public_tests_individual_io"]

    def _issue_description_message(self, execution_results: Dict[str, Any]):
        if not execution_results["compilation_status"]:
            # compilation error occurred
            kwargs = {
                "error_message": execution_results["compilation_error_message"],
            }

            message_content = (
                jinja2.Environment(loader=jinja2.BaseLoader())
                .from_string(self.debugging_setup["compilation_error_template"])
                .render(**kwargs)
            )
        elif execution_results["timeout_error"]:
            # timeout error occurred

            message_content = self.debugging_setup["timeout_error_template"]
        else:
            # code compiled successfully without timeouts

            # retrieve the failed tests
            failed_tests = [
                test_result
                for test_result in execution_results["public_tests_results"]
                if not test_result["status"]
            ]

            runtime_error_test = None
            for test_result in failed_tests:
                if test_result["generated_output"] is None:
                    # runtime error occurred
                    runtime_error_test = test_result

            if runtime_error_test:
                # construct the error message for the runtime error
                kwargs = {
                    "test_input": runtime_error_test["input"],
                    "error_message": runtime_error_test["error_message"],
                }

                message_content = (
                    jinja2.Environment(loader=jinja2.BaseLoader())
                    .from_string(self.debugging_setup["runtime_error_template"])
                    .render(**kwargs)
                )
            else:
                # construct the error message corresponding to a logical error

                if self.debugging_setup["single_test_error_message"]:
                    # construct the error message for a single (the first) failed test
                    first_failed_test = failed_tests[0]

                    kwargs = {
                        "test_input": first_failed_test["input"],
                        "expected_output": first_failed_test["expected_output"],
                        "generated_output": first_failed_test["generated_output"],
                    }

                    message_content = (
                        jinja2.Environment(loader=jinja2.BaseLoader())
                        .from_string(self.debugging_setup["single_test_error_template"])
                        .render(**kwargs)
                    )
                else:
                    # construct the error message covering all failed tests
                    parts = [self.debugging_setup["all_tests_header"]]

                    for idx, test_result in enumerate(failed_tests):
                        kwargs = {
                            "idx": idx + 1,
                            "test_input": test_result["input"],
                            "expected_output": test_result["expected_output"],
                            "generated_output": test_result["generated_output"],
                        }

                        parts.append(
                            jinja2.Environment(loader=jinja2.BaseLoader())
                            .from_string(self.debugging_setup["test_error_template"])
                            .render(**kwargs)
                        )

                    message_content = self.debugging_setup["tests_separator"].join(parts)

        return message_content

    def _get_parsed_response(self, response: Dict[str, Any]):
        assert (
                "public_tests_results" in response and len(response["public_tests_results"]) != 0
        ), "We assume access to at least one test -- provided or generated!"

        all_tests_passed = all([test_result["status"] for test_result in response["public_tests_results"]])

        parsed_outputs = copy.deepcopy(response)
        parsed_outputs["all_tests_passed"] = all_tests_passed

        if not all_tests_passed:
            message_content = self._issue_description_message(execution_results=response)
            parsed_outputs["issue_description"] = message_content

        return parsed_outputs

    def _test_code(self,  task_message: TaskMessage):
        raise NotImplementedError()

    def run(self, task_message: TaskMessage):
        response = self._test_code(task_message)
        parsing_response = self._get_parsed_response(response=response)
        self._update_state(parsing_response)


class CodeTestingAtomicFlowCodeforces(CodeTestingAtomicFlow):
    def _test_code(self, task_message: TaskMessage):
        candidate_solution = task_message.data["code"]
        tests = self._get_tests_io(task_message)

        testing_results = testing_utils_codeforces.evaluate_solution_for_problem(
            candidate_solution=candidate_solution, public_tests_io=tests
        )

        for test_output in testing_results["public_tests_results"]:
            test_output["input"] = "\n".join(test_output["input"])

        return testing_results  # See the "Code evaluators' output per problem" in the README for the output format


class CodeTestingAtomicFlowLeetCode(CodeTestingAtomicFlow):
    def _test_code(self, task_message: TaskMessage):
        candidate_solution = task_message.data["code"]
        tests = self._get_tests_io(task_message)
        python_stub = task_message.data["python_stub"]

        testing_results = testing_utils_leetcode.evaluate_solution_for_problem(
            candidate_solution=candidate_solution, public_tests_io=tests, python_stub=python_stub
        )

        return testing_results  # See the "Code evaluators' output per problem" in the README for the output format
