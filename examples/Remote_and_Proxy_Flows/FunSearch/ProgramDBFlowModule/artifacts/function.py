from . import AbstractArtifact
import dataclasses
import tokenize
import io
from collections.abc import Iterator, MutableSet, Sequence

@dataclasses.dataclass
class FunctionArtifact(AbstractArtifact):
    def __str__(self) -> str:
        
        return_type = f' -> {self.return_type}' if self.return_type else ''
        function = f'def {self.name}({self.args}){return_type}:\n'
        
        if self.docstring:
        # self.docstring is already indented on every line except the first one.
        # Here, we assume the indentation is always two spaces.
            new_line = '\n' if self.body else ''
            function += f'    """{self.docstring}"""{new_line}'
            
        # self.body is already indented.
        function += self.body + '\n\n'
        return function
    
    @staticmethod    
    def _tokenize(code: str) -> Iterator[tokenize.TokenInfo]:
        """Transforms `code` into Python tokens."""
        code_bytes = code.encode()
        code_io = io.BytesIO(code_bytes)
        return tokenize.tokenize(code_io.readline)

    @staticmethod
    def _untokenize(tokens: Sequence[tokenize.TokenInfo]) -> str:
        """Transforms a list of Python tokens into code."""
        code_bytes = tokenize.untokenize(tokens)
        return code_bytes.decode()
    
    def _get_artifacts_called(self) -> MutableSet[str]:
        """Returns the set of all functions called in function."""
        code = str(self.body)
        return set(token.string for token, is_call in
                    self._yield_token_and_is_call(code) if is_call)
    
    def calls_ancestor(self,artifact_to_evolve: str) -> bool:
        """Returns whether the generated function is calling an earlier version."""
        
        for name in self._get_artifacts_called():
            # In `program` passed into this function the most recently generated
            # function has already been renamed to `function_to_evolve` (wihout the
            # suffix). Therefore any function call starting with `function_to_evolve_v`
            # is a call to an ancestor function.
            if name.startswith(f'{artifact_to_evolve}_v') and not name.startswith(self.name):
                return True
        return False

    
    def _yield_token_and_is_call(cls,code: str) -> Iterator[tuple[tokenize.TokenInfo, bool]]:
        """Yields each token with a bool indicating whether it is a function call."""
        
        tokens = cls._tokenize(code)
        prev_token = None
        is_attribute_access = False
        for token in tokens:
            if (prev_token and  # If the previous token exists and
                prev_token.type == tokenize.NAME and  # it is a Python identifier
                token.type == tokenize.OP and  # and the current token is a delimiter
                token.string == "("
                ):  # and in particular it is '('.
                yield prev_token, not is_attribute_access
                is_attribute_access = False
            else:
                if prev_token:
                    is_attribute_access = (
                        prev_token.type == tokenize.OP and prev_token.string == '.'
                    )
                    yield prev_token, False
                    
            prev_token = token
        if prev_token:
            yield prev_token, False

    
    def rename_artifact_calls(self, source_name, target_name) -> str:
        implementation = str(self)
        
        if source_name not in implementation:
            return implementation
        
        modified_tokens = []
        for token, is_call in self._yield_token_and_is_call(implementation):
            if is_call and token.string == source_name:
                # Replace the function name token
                modified_token = tokenize.TokenInfo(
                    type=token.type,
                    string=target_name,
                    start=token.start,
                    end=token.end,
                    line=token.line,
                )
                modified_tokens.append(modified_token)
            else:
                modified_tokens.append(token)
        return self._untokenize(modified_tokens)
