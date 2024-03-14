import dataclasses
from typing import Optional
from .artifacts import AbstractArtifact
import ast
from .artifacts import FunctionArtifact

@dataclasses.dataclass(frozen=True)
class Program:
  """A parsed Python program."""

  # `preface` is everything from the beginning of the code till the first
  # function is found.
  preface: str
  artifacts: list[AbstractArtifact]

  def __str__(self) -> str:
    program = f'{self.preface}\n' if self.preface else ''
    program += '\n'.join([str(f) for f in self.artifacts])
    return program

  def find_artifact_index(self, artifact_name: str) -> int:
    """Returns the index of input function name."""
    
    artifact_names = [a.name for a in self.artifacts]
    count = artifact_names.count(artifact_name)
    if count == 0:
      raise ValueError(
          f'artifact {artifact_name} does not exist in program:\n{str(self)}'
      )
    if count > 1:
      raise ValueError(
          f'artifact {artifact_name} exists more than once in program:\n'
          f'{str(self)}'
      )
    index = artifact_names.index(artifact_name)
    return index

  def get_artifact(self, artifact_name: str) -> AbstractArtifact:
    index = self.find_artifact_index(artifact_name)
    return self.artifacts[index]
  
# TODO: Do this for various types of artifacts (only for functions rn)
class ProgramVisitor(ast.NodeVisitor):
    """Parses code to collect all required information to produce a `Program`.

    Note that we do not store function decorators.
    """

    def __init__(self, sourcecode: str):
        self._codelines: list[str] = sourcecode.splitlines()

        self._preface: str = ''
        self._artifacts: list[AbstractArtifact] = []
        self._current_artifact: Optional[str] = None

    def visit_FunctionDef(self,
                        node: ast.FunctionDef):
        """Collects all information about the function being parsed."""
        if node.col_offset == 0:  # We only care about first level functions.
            self._current_function = node.name
            if not self._artifacts:
                self._preface = '\n'.join(self._codelines[:node.lineno - 1])
                
            function_end_line = node.end_lineno
            body_start_line = node.body[0].lineno - 1
            # Extract the docstring.
            docstring = None
            if isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value,ast.Str):
                docstring = f'  """{ast.literal_eval(ast.unparse(node.body[0]))}"""'
                if len(node.body) > 1:
                    body_start_line = node.body[1].lineno - 1
                else:
                    body_start_line = function_end_line

            self._artifacts.append(FunctionArtifact(
                name=node.name,
                args=ast.unparse(node.args),
                return_type=ast.unparse(node.returns) if node.returns else None,
                docstring=docstring,
                body='\n'.join(self._codelines[body_start_line:function_end_line]),
            ))
        self.generic_visit(node)

    def return_program(self) -> Program:
        return Program(preface=self._preface, artifacts=self._artifacts)
      

def text_to_program(text: str) -> Program:
  """Returns Program object by parsing input text using Python AST."""
  # We assume that the program is composed of some preface (e.g. imports,
  # classes, assignments, ...) followed by a sequence of functions.
  
  #Often happens that it returns a codeblock so remove it
  if text.startswith("```python"):
      text = text[9:]
  if text.endswith("```"):
      text = text[:-3]
  
  tree = ast.parse(text)
  visitor = ProgramVisitor(text)
  visitor.visit(tree)
  return visitor.return_program()

def text_to_artifact(text: str) -> AbstractArtifact:
  """Returns Function object by parsing input text using Python AST."""
  program = text_to_program(text)
  if len(program.artifacts) != 1:
    raise ValueError(f'Only one artifact expected, got {len(program.artifacts)}'
                        f':\n{program.functions}')
  return program.artifacts[0]