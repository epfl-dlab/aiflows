import re
# to run the solution files we're using a timing based approach
import signal
import sys
import threading
# for capturing the stdout
from io import StringIO
from typing import List, Tuple
# used for testing the code that reads from input
from unittest.mock import patch, mock_open

import numpy as np
from pyext import RuntimeModule
from wrapt_timeout_decorator import timeout as wrapt_timeout

import flows.utils as utils

log = logging.get_logger(__name__)
lock = threading.Lock()


def assert_test_format_codeforces(tests: List[Tuple[List[str], str]]):
    assert isinstance(tests, list) or tests is None
    if tests is None:
        return
    for test in tests:
        assert isinstance(test, list)
        assert len(test) == 2
        inputs, outputs = test
        assert isinstance(inputs, list)
        assert isinstance(outputs, str)
        for input in inputs:
            assert isinstance(input, str)


def evaluate_solution_for_problem(
        candidate_solution,
        hidden_tests_io=None,
        public_tests_io=None,
        timeout=10,
        debug=False,
        add_extra_imports=False,
        allow_truncated_io=False,
):
    with lock:
        """See the readme for the output format of this function."""
        if hidden_tests_io is None:
            hidden_tests_io = []
        if public_tests_io is None:
            public_tests_io = []

        if candidate_solution is None:
            results_dict = {
                "compilation_status": False,
                "compilation_error_message": "No code was provided.",
                "timeout_error": False,
                "hidden_tests_results": [
                    {
                        "status": False,
                        "error_message": "No code was provided.",
                        "generated_output": None,
                        "input": test[0],
                        "expected_output": test[1],
                    }
                    for test in hidden_tests_io
                ],
                "public_tests_results": [
                    {
                        "status": False,
                        "error_message": "No code was provided.",
                        "generated_output": None,
                        "input": test[0],
                        "expected_output": test[1],
                    }
                    for test in public_tests_io
                ],
            }
            return results_dict

        @wrapt_timeout(timeout, use_signals=False)
        def run_tests():
            hidden_tests_results = check_correctness(
                candidate_solution, hidden_tests_io, timeout, debug, add_extra_imports, allow_truncated_io
            )
            public_tests_results = check_correctness(
                candidate_solution, public_tests_io, timeout, debug, add_extra_imports, allow_truncated_io
            )

            return hidden_tests_results, public_tests_results

        try:
            hidden_tests_results, public_tests_results = run_tests()
            timeout_error_occurred = False
        except BaseException as e:
            log.info(e)
            hidden_tests_results = {}
            public_tests_results = {}

            hidden_tests_results["compilation_status"] = True
            public_tests_results["compilation_status"] = True
            timeout_error_occurred = True
            hidden_tests_results["error_message"] = "Timeout error."

            hidden_tests_results["results"] = [
                {
                    "status": False,
                    "error_message": hidden_tests_results["error_message"],
                    "generated_output": None,
                    "input": test[0],
                    "expected_output": test[1],
                }
                for test in hidden_tests_io
            ]
            public_tests_results["results"] = [
                {
                    "status": False,
                    "error_message": hidden_tests_results["error_message"],
                    "generated_output": None,
                    "input": test[0],
                    "expected_output": test[1],
                }
                for test in public_tests_io
            ]

        # the compilation status shouldn't depend on the tests
        assert hidden_tests_results["compilation_status"] == public_tests_results["compilation_status"]

        results_dict = {
            "compilation_status": hidden_tests_results["compilation_status"],
            "compilation_error_message": hidden_tests_results["error_message"],
            "timeout_error": timeout_error_occurred,
            "hidden_tests_results": hidden_tests_results["results"],
            "public_tests_results": public_tests_results["results"],
        }

        return results_dict


def check_correctness(
        candidate_solution: str,
        tests: List[Tuple[List[str], str]],
        timeout: int = 6000,
        debug=True,
        add_extra_imports=False,
        allow_truncated_io=True,
):
    """
    wrapping the testing code in a global timeout, based on huggingface code
    """

    assert_test_format_codeforces(tests)
    inputs, outputs = [], []
    if len(tests) > 0:
        inputs, outputs = zip(*tests)

    compilation_error, results = run_test(
        candidate_solution, inputs, outputs, timeout, debug, add_extra_imports, allow_truncated_io
    )

    assert len(results) == len(inputs)

    for result in results:
        assert isinstance(result["generated_output"], str) or result["generated_output"] is None
        assert isinstance(result["status"], bool)
        assert isinstance(result["error_message"], str) or result["error_message"] is None
        assert isinstance(result["input"], list)
        assert isinstance(result["expected_output"], str)

    compilation_status = compilation_error == ""
    if compilation_status:
        compilation_error = None

    return {"compilation_status": compilation_status, "error_message": compilation_error, "results": results}


class TimeoutException(Exception):
    pass


def timeout_handler(signum, frame):
    log.info("alarm went off")
    # return
    raise TimeoutException


signal.signal(signal.SIGALRM, timeout_handler)


# used to capture stdout as a list
# from https://stackoverflow.com/a/16571630/6416660
# alternative use redirect_stdout() from contextlib
class Capturing(list):
    def __enter__(self):
        self._stdout = sys.stdout
        sys.stdout = self._stringio = StringIO()
        # Make closing the StringIO a no-op
        self._stringio.close = lambda x: 1
        return self

    def __exit__(self, *args):
        self.extend(self._stringio.getvalue().splitlines())
        del self._stringio  # free up some memory
        sys.stdout = self._stdout


def run_test(code, inputs, outputs, timeout: int = 6000, debug=True, add_extra_imports=False, allow_truncated_io=True):
    """
    runs the code and tries to match inputs and outputs
    the scraped testcases may be incomplete
    if allow_truncated_io==True, then we ignore an EOF exception at the end of the generated output
    """
    # Disable functionalities that can make destructive changes to the test.

    results = []

    if isinstance(code, list):
        tmp_test = code
    elif isinstance(code, str):
        tmp_test = code.split("\n")
    else:
        raise AssertionError("code must be provided as list of lines or string with \\n linebreaks.")

    # parse the code into code and imports
    import_lines = []
    future_import_lines = []
    code_lines = []
    for x in tmp_test:
        if (not x.startswith("from ")) and (not x.startswith("import ")):
            code_lines.append("\t" + x + "\n")
        else:
            if "__future__" in x:
                future_import_lines.append(x + "\n")
            else:
                import_lines.append(x + "\n")

    # assemble a new solution snippet which wraps the generated solution in a function code()
    new_test = "stdin = sys.stdin\nstdout = sys.stdout\n"
    new_test += '__name__="__main__"\n'
    new_test += "def code():\n"
    for line in code_lines:
        new_test += line

    sol = "\n".join(future_import_lines)
    sol += "import sys\n"
    if add_extra_imports:
        sol += "import time\nimport itertools\nfrom itertools import accumulate, product, permutations, combinations\nimport collections\nfrom collections import Counter, OrderedDict, deque, defaultdict, ChainMap\nfrom functools import lru_cache\nimport math\nfrom math import sqrt, sin, cos, tan, ceil, fabs, floor, gcd, exp, log, log2\nimport fractions\nfrom typing import List, Tuple\nimport numpy as np\nimport random\nimport heapq\nfrom heapq import *\n"
    sol += "\n".join(import_lines) + "\n" + new_test

    if debug:
        log.info(f"sol = {sol}")
    method_name = "code"
    signal.alarm(timeout)

    # convert the solution snippet into a pyext runtime module
    sol_module = None
    try:
        sol_module = RuntimeModule.from_string("tmp_sol", "", sol)
        signal.alarm(0)
    except Exception as e:
        signal.alarm(0)
        if debug:
            log.info(f"type 1 compilation error = {e}")
        for inp, out in zip(inputs, outputs):
            # consider all inputs failed
            results.append(
                {
                    "status": False,
                    "input": inp,
                    "expected_output": out,
                    "generated_output": None,
                    "error_message": repr(e),
                }
            )
        return repr(e), results

    assert sol_module is not None
    signal.alarm(0)

    try:
        method = getattr(sol_module, method_name)  # get_attr second arg must be str
    except:
        signal.alarm(0)
        e = sys.exc_info()
        log.info(f"unable to get function error = {e}")

        for inp, out in zip(inputs, outputs):
            # consider all inputs failed
            results.append(
                {
                    "status": False,
                    "input": inp,
                    "expected_output": out,
                    "generated_output": None,
                    "error_message": repr(e),
                }
            )
        return repr(e), results

    # go through all tests, call our runtime module with the inputs
    # then compare with the reference output
    for index, (test_input, reference_output) in enumerate(zip(inputs, outputs)):

        result_object = {
            "input": test_input,
            "expected_output": reference_output,
        }

        # if the last token of the input is truncated and marked with "..." we delete it
        input_truncated = False
        if "".join(test_input).strip().endswith("...") and allow_truncated_io:
            test_input = test_input[:-1]
            input_truncated = True

        # sometimes the last input token is ""
        # if len(test_input)>0:
        #    if test_input[-1]=="":
        #        test_input = test_input[:-1]

        error_code = None
        with Capturing() as generated_output:
            try:
                call_method(method, test_input)
                # reset the alarm
                signal.alarm(0)
            except Exception as e:
                # runtime error or took too long
                signal.alarm(0)
                error_code = e
                if debug:
                    log.info(f"Call-based runtime error or time limit exceeded error = {repr(e)}{e}")
            signal.alarm(0)

        # in some cases we run into truncated tests
        # in such cases we expect the error code to be None, EOFError or ValueError
        if (
                (input_truncated or reference_output.strip().endswith("..."))
                and allow_truncated_io
                and (error_code is None or isinstance(error_code, EOFError) or isinstance(error_code, ValueError))
        ):

            generated_output = generated_output[:-1]
            reference_output = reference_output.rstrip("...")
            if len(generated_output) == 0:
                # no output left, we pass by default
                result_object.update(
                    **{
                        "status": True,
                        "generated_output": "\n".join(generated_output),
                        "error_message": None,
                    }
                )
                results.append(result_object)
            else:
                result_object.update(
                    **{
                        "status": string_compare(generated_output, reference_output, True),
                        "generated_output": "\n".join(generated_output),
                        "error_message": None,
                    }
                )
                results.append(result_object)

        # if the input and output are not truncated, we don't allow any errors
        elif error_code is not None:
            result_object.update(**{"status": False, "generated_output": None, "error_message": repr(error_code)})
            results.append(result_object)
        # finally, if there are no errors, we expect the output to match the reference output
        else:
            # the execution went well, let's compare the outputs
            result_object.update(
                **{
                    "status": string_compare(generated_output, reference_output, False),
                    "generated_output": "\n".join(generated_output),
                    "error_message": None,
                }
            )
            results.append(result_object)

    return "", results


def string_compare(candidate, correct, truncate_output=False, floating_point_accuracy=0.01):
    candidate = [o.strip().lower() for o in candidate]
    correct = correct.strip().lower()

    # normalize whitespace
    candidate = "\n".join(candidate)
    candidate = re.sub("\s+", " ", candidate).strip()
    correct = re.sub("\s+", " ", correct).strip()

    # split into individual tokens
    candidate = candidate.split(" ")
    correct = correct.split(" ")

    # some tests may be truncated, if we allow this we don't enforce equal length of inputs/outputs
    if not truncate_output:
        if not len(candidate) == len(correct):
            return False

    # if we allow truncated io, the last token of the output may have been corrupted
    if truncate_output:
        correct = correct[:-1]

    # when zip is used for lists of unequal length it will give as many pairs as there are items in the shorter list
    for left, right in zip(candidate, correct):
        if left == right:
            continue

        try:
            int_left = int(left)
            int_right = int(right)
            if int_left == int_right:
                continue
        except ValueError:
            pass

        try:
            float_left = float(left)
            float_right = float(right)
            if np.abs(float_left - float_right) < floating_point_accuracy:
                continue
        except ValueError:
            pass

        return False

    return True


def call_method(method, inputs):
    if isinstance(inputs, list):
        inputs = "\n".join(inputs)

    inputs_line_iterator = iter(inputs.split("\n"))

    # sys.setrecursionlimit(10000)

    # @patch('builtins.input', side_effect=inputs.split("\n"))
    @patch("builtins.open", mock_open(read_data=inputs))
    @patch("sys.stdin", StringIO(inputs))
    @patch("sys.stdin.readline", lambda *args: next(inputs_line_iterator))
    @patch("sys.stdin.readlines", lambda *args: inputs.split("\n"))
    @patch("sys.stdin.read", lambda *args: inputs)
    # @patch('sys.stdout.write', print)
    def _inner_call_method(_method):
        try:
            return _method()
        except SystemExit as e:
            pass
        finally:
            pass

    return _inner_call_method(method)
