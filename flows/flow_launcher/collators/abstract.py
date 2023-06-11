from abc import ABC
from typing import List, Dict


class Collator(ABC):
    def collate_fn(self, batch: List[Dict]) -> List[Dict]:
        raise NotImplementedError("Not implemented")
