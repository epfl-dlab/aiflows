from typing import Any, Dict

from flows.base_flows import AtomicFlow


class VanillaFlow(AtomicFlow):
    SUPPORTS_CACHING = False

    def run(self,
            input_data: Dict[str, Any]) -> Dict[str, Any]:
        return input_data