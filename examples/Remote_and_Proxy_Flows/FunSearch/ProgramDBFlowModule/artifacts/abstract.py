from typing import Any, Optional
import dataclasses


@dataclasses.dataclass
class AbstractArtifact:
    """ Abstract class for artifacts."""
    
    name: str
    args: str
    body: str
    return_type: Optional[str] = None
    docstring: Optional[str] = None

    def __str__(self)->str:
        raise NotImplementedError()
    
    def __setattr__(self, name: str, value: str) -> None:
        # Ensure there aren't leading & trailing new lines in `body`.
        if name == 'body':
            value = value.strip('\n')
        # Ensure there aren't leading & trailing quotes in `docstring``.
        if name == 'docstring' and value is not None:
            if '"""' in value:
                value = value.strip()
                value = value.replace('"""', '')
        super().__setattr__(name, value)
    
    def rename_artifact_calls(self, source_name, target_name) -> str:
        raise NotImplementedError
    
    def text_to_artifact(self):
        raise NotImplementedError
    
    def calls_ancestor(self,artifact_to_evolve: str) -> bool:
        raise NotImplementedError