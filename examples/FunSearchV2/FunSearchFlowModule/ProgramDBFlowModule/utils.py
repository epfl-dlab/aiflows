import numpy as np
import scipy
def add_gaussian_noise(array,mean=0,std=1):
    return array + np.random.normal(mean,std,array.shape)

def get_versioned_function_name(function_name,i):
    pass

def rename_function(implementation,function_name):
    pass

def string_concatenation(strings,split_char='\n\n'):
    pass

def make_header_like(implementation,function_name):
    pass

def rename_function_calls(implementation,function_name):
    pass

def extract_template_from_program(program):
    pass


def _softmax(logits: np.ndarray, temperature: float, epsilon = 1e-6) -> np.ndarray:
    """Returns the tempered softmax of 1D finite `logits`."""
    if not np.all(np.isfinite(logits)):
        non_finites = set(logits[~np.isfinite(logits)])
        raise ValueError(f'`logits` contains non-finite value(s): {non_finites}')
    if not np.issubdtype(logits.dtype, np.floating):
        logits = np.array(logits, dtype=np.float32)

    result = scipy.special.softmax(logits / temperature, axis=-1)
    
    #Non zero mass to prevent zero probabilities
    result += epsilon  # Add epsilon to prevent zeros
    result /= np.sum(result, axis=-1, keepdims=True)  # Normalize

    # Ensure that probabilities sum to 1 to prevent error in `np.random.choice`.
    index = np.argmax(result)
    result[index] = 1 - np.sum(result[0:index]) - np.sum(result[index+1:])
    return result