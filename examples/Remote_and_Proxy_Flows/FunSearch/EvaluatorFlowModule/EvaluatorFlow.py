from aiflows.base_flows import AtomicFlow
from typing import Dict, Any
import os
from aiflows.utils import logging
import ast
import signal

log = logging.get_logger(f"aiflows.{__name__}")

class TimeoutException(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutException("Execution timed out")

class EvaluatorFlow(AtomicFlow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.evaluator_py_file = self.flow_config["py_file"]
        

        # Create a local namespace for the class
        self.local_namespace = {}
        self.load_functions()
        self.function_to_run_name = self.flow_config["function_to_run_name"]
        assert self.function_to_run_name in self.local_namespace, f"Function {self.function_to_run_name} not found in {self.evaluator_py_file_path}"
        self.function_to_run = self.local_namespace.get(self.function_to_run_name)
     
        self.test_inputs = self.flow_config["test_inputs"]
        self.timeout_seconds = self.flow_config["timeout_seconds"]
        self.local_namespace = {}

    def load_functions(self):
        functions = self.evaluator_py_file
        try:
            # Execute the content of the file in the global namespace
            exec(functions,self.local_namespace)
        except Exception as e:
            log.error(f"Error functions: {e}")
            raise e

    def run_function_with_timeout(self,program, **kwargs):
        # Set up a signal handler for the alarm
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(self.timeout_seconds)  # Set the alarm for the specified timeout
        
        try:
            result = self.function_to_run(program,**kwargs)
            return True, result
        except TimeoutException as e:
            return False, str(e)
        except Exception as e:
            return False, str(e)
        finally:
            signal.alarm(0)  

    def evaluate_program(self, program, **kwargs):
        try:
            runs_ok, test_output = self.run_function_with_timeout(program, **kwargs)
            
            return runs_ok, test_output

        except Exception as e:
            log.debug(f"Error defining runnin program: {e} (could be due to syntax error from LLM)")
            return False, None


    def analyse(self, program):
        scores_per_test = {}
        for test_input in self.test_inputs.values():
            if test_input is None:
                runs_ok,test_output = self.evaluate_program(program)
            else:
                runs_ok,test_output = self.evaluate_program(program, **test_input)  # Run the program
            if runs_ok and test_output is not None:  # and not utils.calls_ancestor(program) (TODO: check what they mean by this in the paper)
                scores_per_test[str(test_input)] = test_output

        return scores_per_test

    def run(self, input_data: Dict[str, Any]):
      
        scores_per_test = self.analyse(input_data["artifact"])
        
        response = {"operation": "register_program", "scores_per_test": scores_per_test, "artifact": input_data["artifact"], "island_id": input_data.get("island_id",None) }
     
        return response
