from typing import Dict, Any

from flows.outputs_transformations.abstract import OutputsTransformation


class Rename(OutputsTransformation):
    def __init__(self,
                 old_key2new_key: Dict[str, str],
                 **kwargs):
        super().__init__(**kwargs)
        self.old_key2new_key = old_key2new_key

    def __call__(self, outputs: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        for old_key, new_key in self.old_key2new_key.items():
            if old_key in outputs:
                outputs[new_key] = outputs.pop(old_key)

        return outputs
