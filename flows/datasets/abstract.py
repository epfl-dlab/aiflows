import random


class AbstractDataset:
    """
    A dataset implements 2 functions
        - __len__  (returns the number of samples in our dataset)
        - __getitem__ (returns a sample from the dataset at the given index idx)
    """

    def __init__(self, params):
        super().__init__()
        self.params = params
        self.random_state = random.Random(self.params.get("seed", 123))

    def __len__(self):
        raise NotImplementedError()

    def __getitem__(self, idx):
        raise NotImplementedError()

    def __iter__(self):
        for idx in range(len(self)):
            yield self[idx]

    def _load_data(self):
        raise NotImplementedError()
