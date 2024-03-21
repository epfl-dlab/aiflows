from aiflows.backends.api_info import ApiInfo
import os
from aiflows import logging
from aiflows.utils.general_helpers import read_yaml_file, quick_load_api_keys
from aiflows.base_flows import AtomicFlow
from aiflows.flow_launchers import FlowLauncher
from aiflows.utils.general_helpers import quick_load
from aiflows.workers import run_dispatch_worker_thread
from aiflows.messages import FlowMessage
import argparse
logging.set_verbosity_debug()
dependencies = [
    {
         "url": "aiflows/FunSearchFlowModule",
         "revision": "FunSearchFlowModule"
    }
]
from aiflows import flow_verse
flow_verse.sync_dependencies(dependencies)

from flow_modules.aiflows.FunSearchFlowModule.Loader import Loader

import pandas as pd
import sys
from copy import deepcopy
import requests
from aiflows.utils import serve_utils
import time


def load_problem(id, ds_location = "./data/codeforces.jsonl.gz"):
    
    def make_problem_descriptions_str(row):
        
        def write_public_tests_individual_io_str(row):
            public_tests = row.public_tests_individual_io
            tests = ""
            for i,test in enumerate(public_tests):
                input = test[0]
                output = test[1]
                tests += f"Test {i+1}:\n  Input: {input}\n  Output: \'{output}\'\n"
            return tests
        
        problem_descritption = row.problem_description
        input_descriptions = row.input_description
        ouput_descriptions = row.output_description
        public_tests = write_public_tests_individual_io_str(row)
        
        problem_description_str = f"Problem Description:\n{problem_descritption}\n\n"
        input_description_str = f"Input Description:\n{input_descriptions}\n\n"
        output_description_str = f"Output Description:\n{ouput_descriptions}\n\n"
        public_tests_str = f"Public Tests:\n{public_tests}\n"
        
        final_str = problem_description_str + input_description_str + output_description_str +public_tests_str
        return final_str
    
    df = pd.read_json(ds_location, lines=True, compression='gzip')
    row = df[df.id == id].iloc[0]

    assert row.non_unique_output == False, "Problem has non unique output. Not supported yet"

    problem_description = make_problem_descriptions_str(row)
    public_test = row.public_tests_individual_io
    tests = {}
    test_counter = 1

    for public_test in public_test:
        tests["test_"+str(test_counter)] = {"tests_inputs": public_test[0], "expected_outputs": public_test[1]}
        test_counter += 1
        
    for hidden_test in row.hidden_tests_io:
        tests["test_"+str(test_counter)] = {"tests_inputs": hidden_test[0], "expected_outputs": hidden_test[1]}
        test_counter += 1
    
    return  tests, problem_description 

def download_codeforces_data(data_folder_path,file_name):
    print("Downloading data....")
    os.makedirs(data_folder_path, exist_ok=True)
    url = "https://github.com/epfl-dlab/cc_flows/raw/main/data/codeforces/codeforces.jsonl.gz"
    response = requests.get(url, stream=True)
    
    if response.status_code == 200:
        with open(os.path.join(data_folder_path,file_name), 'wb') as file:
            for chunk in response:
                file.write(chunk)
        print("Download complete")
    else:
        print("Failed to download data", response.status_code)
        
def get_config_from_path(root_dir, config_name):
    cfg_path = os.path.join(root_dir, config_name)
    return read_yaml_file(cfg_path)

def get_configs(problem_id):
    tests,  problem_description = load_problem(problem_id)
    
    path = os.path.join(".", "FunSearchFlowModule/FunSearchFlowModule/FunSearch.yaml")
    funsearch_cfg = read_yaml_file(path)
       
    evaluate_function_file_path: str = "./cf_functions.py"
    evaluate_function_name: str = "evaluate"
    evolve_function_name:str = "solve_function"
     
    loader = Loader(file_path = evaluate_function_file_path, target_name = evaluate_function_name)
    evaluate_function: str= loader.load_target()
    evaluate_file_full_content = loader.load_full_file()
    
    evaluate_file_full_content = f"\"\"\"{problem_description}\"\"\"\n\n" + evaluate_file_full_content
    
    #~~~~~ ProgramDBFlow Overrides ~~~~~~~~
    funsearch_cfg["subflows_config"]["ProgramDBFlow"]["evaluate_function"] = evaluate_function
    funsearch_cfg["subflows_config"]["ProgramDBFlow"]["evaluate_file_full_content"] = evaluate_file_full_content
    funsearch_cfg["subflows_config"]["ProgramDBFlow"]["artifact_to_evolve_name"] = evolve_function_name
    
    if len(tests) > 0:
        first_test = tests["test_1"]

        dummy_solution = f"def {evolve_function_name}(input) -> str:" +\
            "\n    \"\"\"Attempt at solving the problem given the input input and returns the predicted output (see the top of the file for problem description)\"\"\"" +\
            f"\n    return \'{first_test['expected_outputs']}\'\n"

    
    else:
        dummy_solution = f"def {evolve_function_name}(input) -> str:" +\
            "\n    \"\"\"Attempt at solving the problem given the input input and returns the predicted output (see the top of the file for problem description)\"\"\"" +\
            f"\n    return 0.0\"\"\n"
    
    #~~~~~~~~~~Evaluator overrides~~~~~~~~~~~~
    funsearch_cfg["subflows_config"]["EvaluatorFlow"]["py_file"] = evaluate_file_full_content
    funsearch_cfg["subflows_config"]["EvaluatorFlow"]["run_error_score"] = -1
    funsearch_cfg["subflows_config"]["EvaluatorFlow"]["function_to_run_name"] = evaluate_function_name
    funsearch_cfg["subflows_config"]["EvaluatorFlow"]["test_inputs"] = tests
    #Hides test inputs from LLM (necessary for hidden tests. Makes same setup as in a real contest.)
    funsearch_cfg["subflows_config"]["EvaluatorFlow"]["use_test_input_as_key"] = False
   
    
    #~~~~~~~~~~Sampler overrides~~~~~~~~~~~~
    api_information = [ApiInfo(backend_used="openai", api_key=os.getenv("OPENAI_API_KEY"))]
    quick_load_api_keys(funsearch_cfg, api_information, key="api_infos")    
    funsearch_cfg["subflows_config"]["SamplerFlow"]["subflows_config"]["Sampler"]["system_message_prompt_template"]["partial_variables"] = \
        {
            "evaluate_name": evaluate_function_name,
            "evolve_name": evolve_function_name,
            "artifacts_per_prompt": 2
        }
        
        
    return funsearch_cfg, dummy_solution


FLOW_MODULES_PATH = "./"


if __name__ == "__main__":
    jwt = os.getenv("COLINK_JWT")
    addr = os.getenv("LOCAL_COLINK_ADDRESS")
    cl = serve_utils.start_colink_component(
        "FunSearch",
         {"jwt": jwt, "addr": addr}
    )
    
    problem_id = "1789B" #put the problem id here
    
      
    if not os.path.exists("./data/codeforces.jsonl.gz"):
        download_codeforces_data("./data", "codeforces.jsonl.gz")
   
    funsearch_cfg, dummy_solution = get_configs(problem_id)
    
    
    
    #Serve Program Database and get its flow type explicitly
    pdb_flow_type = funsearch_cfg["subflows_config"]["ProgramDBFlow"].get("flow_type", "ProgramDBFlow_served")
    serve_utils.recursive_serve_flow(
        cl=cl,
        flow_type=pdb_flow_type,
        default_config=funsearch_cfg["subflows_config"]["ProgramDBFlow"],
        default_state=None,
        default_dispatch_point="coflows_dispatch",
    )
    
    #Serve the rest
    serve_utils.recursive_serve_flow(
        cl=cl,
        flow_type="FunSearch_served",
        default_config=funsearch_cfg,
        default_state=None,
        default_dispatch_point="coflows_dispatch",
    )
    
    # run_dispatch_worker_thread(cl, dispatch_point="coflows_dispatch", flow_modules_base_path=FLOW_MODULES_PATH)
    # run_dispatch_worker_thread(cl, dispatch_point="coflows_dispatch", flow_modules_base_path=FLOW_MODULES_PATH)
    # run_dispatch_worker_thread(cl, dispatch_point="coflows_dispatch", flow_modules_base_path=FLOW_MODULES_PATH)
 
    config_overrides = None
    #Mount ProgramDBFlow first to get it's flow ref
    pdb_proxy_flow = serve_utils.recursive_mount(
        cl=cl,
        client_id="local",
        flow_type=pdb_flow_type,
        config_overrides=config_overrides,
        initial_state=None,
        dispatch_point_override=None,
    )
    
    #add flow ref for PDB
    pdb_flow_ref = pdb_proxy_flow.flow_config["flow_ref"]
   
    config_overrides = {
        "subflows_config": {
            "SamplerFlow": {
                "subflows_config": {
                    "ProgramDB": {
                        "flow_ref": pdb_flow_ref
                    }
                }
            },
            "ProgramDBFlow": {
                "flow_ref": pdb_flow_ref
            }
        },
    }
    
    funsearch_proxy = serve_utils.recursive_mount(
        cl=cl,
        client_id="local",
        flow_type="FunSearch_served",
        config_overrides=config_overrides,
        initial_state=None,
        dispatch_point_override=None,
    )
    
    input_message = FlowMessage(
        data= {"artifact": dummy_solution, "forward_to": "EvaluatorFlow"},
        src_flow="Coflow team",
        dst_flow=funsearch_proxy.flow_config["name"],
        is_input_msg=True
    )
    funsearch_proxy.tell(input_message)
    
    input_message = FlowMessage(
        data= {"retrieved": False, "forward_to": "SamplerFlow"},
        src_flow="Coflow team",
        dst_flow=funsearch_proxy.flow_config["name"],
        is_input_msg=True
    )
    
    funsearch_proxy.tell(input_message)
    wait_time = 180
    print(f"Waiting {wait_time} seconds  before requesting result...")
    time.sleep(wait_time)

    input_message = FlowMessage(
        data= {"operation": "get_best_programs_per_island", "forward_to": "ProgramDBFlow"},
        src_flow="Coflow team",
        dst_flow=funsearch_proxy.flow_config["name"],
        is_input_msg=True
    )
    
    future = funsearch_proxy.ask(input_message)
    print("waiting for response....")
    response = future.get_data()
    print(response)
