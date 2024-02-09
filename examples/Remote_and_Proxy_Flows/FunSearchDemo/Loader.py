import ast
import os
import yaml

class Loader:
    def __init__(self, file_path, target_name):
        self.py_file_path = file_path
        self.target_name = target_name

        if not os.path.exists(file_path):
            raise ValueError(f"File {file_path} does not exist")

        with open(file_path, 'r') as file:
            self.source_code = file.read()

    def load_target(self):
        if self.py_file_path.endswith('.yaml'):
            return self.load_yaml()
        else:
            return self.load_code()
    
    def load_full_file(self):
        return self.source_code

    def load_code(self):
        # Parse the source code into an abstract syntax tree (AST)
        tree = ast.parse(self.source_code)

        # Find the target node (FunctionDef, ClassDef, or variable)
        target_node = None
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.name == self.target_name:
                target_node = node
                break
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == self.target_name:
                        target_node = node
                        break

        if target_node is not None:
            # Extract the source code of the target
            target_source_code = ast.unparse(target_node)
            return target_source_code
        else:
            raise ValueError(f"Target '{self.target_name}' not found in the module.")

    def load_yaml(self):
        try:
            with open(self.py_file_path, 'r') as yaml_file:
                yaml_content = yaml.safe_load(yaml_file)
            return yaml_content
        except yaml.YAMLError as e:
            raise ValueError(f"Error loading YAML file: {e}")

