import os
import pickle


def load_pickle(pickle_path: str):
    # Check if the provided path is valid
    if not os.path.isfile(pickle_path):
        raise FileNotFoundError(f"Checkpoint file not found at {pickle_path}")

    # Load data from the checkpoint file using pickle
    with open(pickle_path, 'rb') as file:
        data = pickle.load(file)

    return data
