
import ast
import itertools
import numpy as np
from typing import List

def solve(solve_function: str,input: List[str], expected_output: str) -> str:
    """function used to run the solve function on input *kwargs and return the the predicted output
    
    :param solve_function: the function to run (the solve function below as a string)
    :type solve_function: str
    :param kwargs: the inputs to the solve function
    :type kwargs: List[str]
    """
    local_namespace = {}
    exec(solve_function,local_namespace)
    found_name, program_name = get_function_name_from_code(solve_function)
    
    if not found_name:
        raise ValueError(f"Function name not found in program: {solve_function}")
    
    solve_fn = local_namespace.get(program_name)
    
    prediction = solve_fn(input)
    
    prediction = prediction.split()
    expected_output = expected_output.split()
    
    if len(prediction) != len(expected_output):
        raise ValueError(f"Invalid Format of prediction")
    
    for i in range(len(prediction)):
        if prediction[i] != expected_output[i]:
            return False
    
    return True

def evaluate(solve_function: str, tests_inputs: List[str], expected_outputs: str) -> float:
    """Returns the score of the solve function we're evolving based on the tests_inputs and expected_outputs.
    Scores are between 0 and 1, unless the program fails to run, in which case the score is -1.
    """
    if solve(solve_function,tests_inputs,expected_outputs) == True:
        return 1.0
    return 0.0


def get_function_name_from_code(code):
    tree = ast.parse(code)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            return True, node.name

    # something is wrong
    return False, None




    
    