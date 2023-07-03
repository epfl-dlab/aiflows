import re
import threading
from subprocess import Popen, PIPE, TimeoutExpired
from typing import List, Tuple

import flows.utils as utils

log = logging.get_logger(__name__)
lock = threading.Lock()


def evaluate_solution_for_problem(
        candidate_solution,
        python_stub,
        hidden_tests_io=None,
        public_tests_io=None,
        timeout=10,
        debug=False,
        add_extra_imports=False,
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

        hidden_tests_results = check_correctness(
            candidate_solution, python_stub, hidden_tests_io, timeout, debug, add_extra_imports
        )
        public_tests_results = check_correctness(
            candidate_solution, python_stub, public_tests_io, timeout, debug, add_extra_imports
        )

        # the compilation status shouldn't depend on the tests
        if len(hidden_tests_io) > 0 and len(public_tests_io) > 0:
            assert hidden_tests_results["compilation_status"] == public_tests_results["compilation_status"]

        compilation_status = True
        error_message = None
        timeout_error = False

        if len(hidden_tests_io) > 0:
            compilation_status = compilation_status and hidden_tests_results["compilation_status"]
            error_message = hidden_tests_results["error_message"]
            timeout_error = timeout_error or hidden_tests_results["timeout_error"]

        if len(public_tests_io) > 0:
            compilation_status = compilation_status and public_tests_results["compilation_status"]
            error_message = public_tests_results["error_message"]
            timeout_error = timeout_error or public_tests_results["timeout_error"]

        results_dict = {
            "compilation_status": compilation_status,
            "compilation_error_message": error_message,
            "timeout_error": timeout_error,
            "hidden_tests_results": hidden_tests_results["results"],
            "public_tests_results": public_tests_results["results"],
        }

        return results_dict


def check_correctness(
        candidate_solution: str,
        python_stub: str,
        tests: List[Tuple[List[str], str]],
        timeout: int = 6000,
        debug=True,
        add_extra_imports=False,
):
    compilation_status = True
    compilation_error = None
    results = []
    timeout_occurred = False

    for idx, test in enumerate(tests):
        inp, out, expl = test
        result = one_test(
            candidate_solution, python_stub, inp, out, timeout=timeout, debug=debug, add_extra_imports=add_extra_imports
        )
        error_message = result["error_message"]

        if error_message is not None:
            if "syntaxerror" in error_message.lower():
                compilation_status = False
                compilation_error = error_message
            if "timeout" in error_message.lower():
                timeout_occurred = True
        results.append(result)

        if timeout_occurred:
            break

    if timeout_occurred:
        return {
            "compilation_status": True,
            "timeout_error": True,
            "error_message": "Timeout error.",
            "results": results,
        }

    return {
        "compilation_status": compilation_status,
        "timeout_error": False,
        "error_message": compilation_error,
        "results": results,
    }


def one_test(candidate_solution, python_stub, inp, out, timeout=10, debug=False, add_extra_imports=False):
    python_stub = python_stub.strip()
    candidate_solution = candidate_solution.strip()

    out = out.replace("null", "None").replace("true", "True").replace("false", "False")

    # reformat the solution and parse class and method name
    class_def, signature = python_stub.split("    def ")
    class_name = class_def.split("class ")[1].strip().rstrip(":")
    func_name, _ = signature.split("(")

    # reformatting the input
    first_param = r"^\w+\s\=\s"
    later_params = r",\s\w+\s\=\s"

    inp = re.sub(first_param, "", inp)
    inp = re.sub(later_params, ", ", inp)

    # we add custom code to invoke the solution
    before_output = "AFTER THIS COMES OUR OWN GENERATED OUTPUT !@#!@!"
    after_output = "AFTER THIS COMES OUR VERDICT !@#!@!"

    if add_extra_imports:
        sol = f"""
from collections import *
from math import *
import math
from functools import *
from heapq import *
import heapq
import itertools
from itertools import *
import bisect
from bisect import *
"""
    else:
        sol = ""

    sol += f"""
from typing import List, Tuple, Optional
{candidate_solution}
sfohsdfdsfjhsdkfjhsdkjfh = {class_name}()
res = sfohsdfdsfjhsdkfjhsdkjfh.{func_name}({inp})

def nested_list_convert(inp):
    try:
        try:
            inp = list(inp)
        except BaseException as e:
            return inp
        out = []
        for i in inp:
            out.append(nested_list_convert(i))
    except BaseException as e:
        return inp
    return out

matching = False
matching = matching or res == {out}
matching = matching or nested_list_convert(res) == {out}
matching = matching or nested_list_convert(res) == nested_list_convert({out})
matching = matching or str({out})==str(res).replace("{{","[").replace("(","[").replace("}}","]").replace(")","]")
matching = matching or str({out})==str(res).replace("{{","[").replace("(","[").replace("}}","]").replace(")","]")
print("res: ", res)
print("out: ", {out})
print("{before_output}")
print(res)
print("{after_output}")
print(matching)
"""

    cmd = "python3"

    proc = Popen([cmd, "-c", sol], stdin=PIPE, stdout=PIPE, stderr=PIPE)

    result_object = {"input": inp, "expected_output": out.strip('"')}

    try:
        stdout, stderr = proc.communicate("", timeout=timeout)
    except TimeoutExpired as e:
        if debug:
            log.info(f"Timeout error, timeout={timeout}")
        result_object.update({"status": False, "error_message": "Timeout error.", "generated_output": None})
        return result_object

    finally:
        proc.kill()

    stdout = stdout.decode()
    stderr = stderr.decode().lower()

    if stderr == "":
        # No compilation or runtime error
        stderr = None
    else:
        # Runtime or compilation error (distinction is made by the presence of "syntaxerror" in the error message)
        result_object.update(**{"status": False, "error_message": stderr, "generated_output": None})
        return result_object

    try:
        generated_output = stdout.split(before_output)[1]
        generated_output, verdict = generated_output.split(after_output)
        result_object.update(
            **{
                "status": verdict.strip() == "True",
                "error_message": stderr,
                "generated_output": generated_output.strip(),
            }
        )
        return result_object
    except IndexError as e:
        raise Exception(f"An unexpected error has occurred while parsing the following generated output: {stdout}")
        # Used in debugging
        # log.info(e)
        # result_object.update(
        #     **{"status": False, "error_message": "The output couldn't be parsed", "generated_output": None}
        # )
        # return result_object
