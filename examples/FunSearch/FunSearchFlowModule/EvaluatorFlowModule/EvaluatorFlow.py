from aiflows.base_flows import AtomicFlow
from typing import Dict, Any
import os
from aiflows.utils import logging
import ast
import signal
from aiflows.interfaces.key_interface import KeyInterface
log = logging.get_logger(f"aiflows.{__name__}")
import threading
class TimeoutException(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutException("Execution timed out")

class EvaluatorFlow(AtomicFlow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.evaluator_py_file = self.flow_config["py_file"]
        self.run_error_score = self.flow_config["run_error_score"]

        # Create a local namespace for the class
        self.local_namespace = {}
        self.load_functions()
        self.function_to_run_name = self.flow_config["function_to_run_name"]
        assert self.function_to_run_name in self.local_namespace, f"Function {self.function_to_run_name} not found in {self.evaluator_py_file_path}"
        self.function_to_run = self.local_namespace.get(self.function_to_run_name)

        self.test_inputs = self.flow_config["test_inputs"]
        self.timeout_seconds = self.flow_config["timeout_seconds"]
        self.local_namespace = {}
        
        
        select_island_id_with_default = lambda data_dict,**kwargs: {**data_dict,**{"island_id":  data_dict.get("island_id", None)}} 
        
        self.output_interface = KeyInterface(
            keys_to_set= {"operation": "register_program", "forward_to": "ProgramDBFlow"},
            additional_transformations= [select_island_id_with_default],
            keys_to_select= ["artifact", "scores_per_test", "island_id", "operation","forward_to"]
        )

    
    def load_functions(self):
        file_content = self.evaluator_py_file
        try:
            # Parse the AST (Abstract Syntax Tree) of the file content
            parsed_ast = ast.parse(file_content)

            # Iterate over the parsed AST nodes
            for node in parsed_ast.body:
                # Check if the node is an import statement
                if isinstance(node, ast.Import):
                    # Execute the import statement in the global namespace
                    exec(compile(ast.Module(body=[node],type_ignores=[]), '<ast>', 'exec'), self.local_namespace)
                elif isinstance(node, ast.ImportFrom):
                    # Execute the import-from statement in the global namespace
                    exec(compile(ast.Module(body=[node],type_ignores=[]), '<ast>', 'exec'), self.local_namespace)

            # Execute the content of the file in the global namespace
            exec(file_content, self.local_namespace)
        except Exception as e:
            log.error(f"Error functions: {e}")
            raise e
        
    def run_function_with_timeout(self, program, **kwargs):
        self.result = None
        self.exception = None

        # Function to run with a timeout
        def target():
            try:
                result = self.function_to_run(program, **kwargs)
                self.result = result
            except Exception as e:
                self.exception = e

        # Create a separate thread to run the target function
        thread = threading.Thread(target=target)
        thread.start()

        # Wait for the specified timeout
        thread.join(self.timeout_seconds)

        # If thread is still alive, it means the timeout has occurred
        if thread.is_alive():
            # Raise a TimeoutException
            thread.terminate()
            return False, f"Function execution timed out after {self.timeout_seconds} seconds"

        # If thread has finished execution, check if there was an exception
        if self.exception is not None:
            return False, str(self.exception)

        # If no exception, return the result
        return True, self.result

 

    def evaluate_program(self, program, **kwargs):
        try:
            runs_ok, test_output = self.run_function_with_timeout(program, **kwargs)
            
            return runs_ok, test_output

        except Exception as e:
            log.debug(f"Error defining runnin program: {e} (could be due to syntax error from LLM)")
            return False, e

    

    def analyse(self, program):
        
        #Often happens that it returns a codeblock so remove it
        if program.startswith("```python"):
            program = program[9:]
        if program.endswith("```"):
            program = program[:-3]
        
        scores_per_test = {}
        for key,test_input in self.test_inputs.items():
            
            test_input_key = str(test_input) if self.flow_config["use_test_input_as_key"] else key
            
            if test_input is None:
                runs_ok,test_output = self.evaluate_program(program)
            else:
                runs_ok,test_output = self.evaluate_program(program, **test_input)  # Run the program
            
            if runs_ok and test_output is not None:  # and not utils.calls_ancestor(program) (TODO: check what they mean by this in the paper)
                scores_per_test[test_input_key] = {"score": test_output, "feedback": "No feedback available."}
                log.debug(f"Program run successfully for test case {test_input_key} with score: {test_output}")
            else:
                log.debug(f"Error running Program for test case {test_input_key}. Error is : {test_output} (could be due to syntax error from LLM)")
                scores_per_test[test_input_key] = {"score": self.run_error_score, "feedback": str(test_output)}

        return scores_per_test

    def run(self, input_data: Dict[str, Any]):
        
        scores_per_test = self.analyse(input_data["artifact"])
       
        response = {**input_data, **{"scores_per_test": scores_per_test}}
        
        response = self.output_interface(response)
        breakpoint()
        return response
