import ast
import itertools
import numpy as np

def solve(priority_functio_str: str,n: int) -> np.ndarray:
    """Returns a large cap set in `n` dimensions."""
    local_namespace = {}
    exec(priority_functio_str,local_namespace)
    found_name, program_name = get_function_name_from_code(priority_functio_str)
    if not found_name:
        raise ValueError(f"Function name not found in program: {priority_functio_str}")
    
    priority = local_namespace.get(program_name)
    
    all_vectors = np.array(list(itertools.product((0, 1, 2), repeat=n)), dtype=np.int32)

    # Powers in decreasing order for compatibility with `itertools.product`, so
    # that the relationship `i = all_vectors[i] @ powers` holds for all `i`.
    powers = 3 ** np.arange(n - 1, -1, -1)

    # Precompute all priorities.
    priorities = np.array([priority(tuple(vector), n) for vector in all_vectors],dtype = np.float32)

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

def evaluate(priority_functio_str:str, n: int) -> int:
    """Returns the size of an `n`-dimensional cap set."""
    capset = solve(priority_functio_str,n)
    return len(capset)


def get_function_name_from_code(code):
    tree = ast.parse(code)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            return True, node.name

    # something is wrong
    return False, None

def priority_function(el: tuple[int, ...], n: int) -> float:
    """Returns the priority with which we want to add `element` to the cap set."""
    return 0.0



    
    