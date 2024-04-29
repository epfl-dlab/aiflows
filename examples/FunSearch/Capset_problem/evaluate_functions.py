
"""Finds large cap sets."""

import ast
import itertools
import numpy as np
from typing import List, Callable

### !!! Don't Touch this Function !!! ###
def get_function_name_from_code(code):
    tree = ast.parse(code)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            return True, node.name

    # something is wrong
    return False, None

### !!! Don't Touch this Function !!! ###
def get_function(function_str: str):
    local_namespace = {}
    
    exec(function_str,local_namespace)
    found_name, program_name = get_function_name_from_code(function_str)
    
    if not found_name:
        raise ValueError(f"Function name not found in program: {function_str}")
    
    priority_fn = local_namespace.get(program_name)
    return priority_fn

# Define Your evaluate function here
def evaluate(function_str: str, n: int) -> int:
    """Returns the size of an `n`-dimensional cap set."""
    
    # This line must always be in evaluate function (converts generated string sample to callable)
    priority_fn = get_function(function_str) 
    capset = solve(priority_fn,n)
    return len(capset)

# Solve function, used in evaluate
def solve(priority_fn: Callable, n: int) -> np.ndarray:
    """Returns a large cap set in `n` dimensions."""
    
    all_vectors = np.array(list(itertools.product((0, 1, 2), repeat=n)), dtype=np.int32)

    # Powers in decreasing order for compatibility with `itertools.product`, so
    # that the relationship `i = all_vectors[i] @ powers` holds for all `i`.
    powers = 3 ** np.arange(n - 1, -1, -1)

    # Precompute all priorities.
    priorities = np.array([priority_fn(tuple(vector), n) for vector in all_vectors])

    # Build `capset` greedily, using priorities for prioritization.
    capset = np.empty(shape=(0, n), dtype=np.int32)
    while np.any(priorities != -np.inf):
        # Add a vector with maximum priority to `capset`, and set priorities of
        # invalidated vectors to `-inf`, so that they never get selected.
        max_index = np.argmax(priorities)
        vector = all_vectors[None, max_index]  # [1, n]
        blocking = np.einsum('cn,n->c', (- capset - vector) % 3, powers)  # [C]
        priorities[blocking] = -np.inf
        priorities[max_index] = -np.inf
        capset = np.concatenate([capset, vector], axis=0)

    return capset




