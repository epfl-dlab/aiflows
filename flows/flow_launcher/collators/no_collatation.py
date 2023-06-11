from . import Collator
from typing import List, Dict


class NoCollationCollator(Collator):
    def __init__(self):
        pass

    def collate_fn(self, batch: List[Dict]) -> List[Dict]:
        return batch
