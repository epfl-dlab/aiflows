from IPython.core.magic import register_cell_magic
from omegaconf import OmegaConf
import os
import pandas as pd
import requests
from aiflows.utils.general_helpers import read_yaml_file
from flow_modules.aiflows.FunSearchFlowModule.Loader import Loader

NICE_PROGRAM_TEMPLATE = \
"""
### Rank: {rank}
### Score: {score}
### Island ID: {island_id}
### Program:
{program}
"""

@register_cell_magic
def compile_and_writefile(line, cell):
    # Compile the code in the cell
    compiled_code = compile(cell, '<string>', 'exec')
    #check if all directories exist and create them if they don't   
    # Extract the directory path from the file path
    directory = os.path.dirname(line)

    # Check if the directory exists
    if not os.path.exists(directory):
        # Create the directory if it doesn't exist
        os.makedirs(directory)
        # Write the compiled code to a file
    with open(line, 'w') as f:
        f.write(cell)
        
    
def dict_to_yaml(dictionary, output_file):
    """
    Convert a dictionary to YAML using OmegaConf and write to a file.

    :param dictionary: Dictionary to convert.
    :type dictionary: dict
    :param output_file: Path to the output YAML file.
    :type output_file: str
    """
    # Convert dictionary to OmegaConf config object
    config = OmegaConf.create(dictionary)
    
    directory = os.path.dirname(output_file)

    # Check if the directory exists
    if not os.path.exists(directory):
        # Create the directory if it doesn't exist
        os.makedirs(directory)

    #wirite file in yaml format
    with open(output_file, 'w') as f:
        OmegaConf.save(config, f.name)


def make_best_program_per_island_nice(response):
    best_island_programs = response["retrieved"]['best_island_programs']
    nice_programs = []
    for program in best_island_programs:
        rank = program['rank']
        score = program['score']
        prgm = program['program']
        island_id = program['island_id']
        nice_program = NICE_PROGRAM_TEMPLATE.format(
            rank=rank,
            score=score,
            program=prgm,
            island_id=island_id
        )
        nice_programs.append(nice_program)
    return nice_programs
        
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

def get_configs_cf(problem_id, ds_location="./data/codeforces.jsonl.gz"):
    tests,  problem_description = load_problem(problem_id,ds_location=ds_location)
    
    path = os.path.join("flow_modules/aiflows/FunSearchFlowModule", "demo.yaml")
    funsearch_cfg = read_yaml_file(path)
       
    evaluate_function_file_path: str = os.path.join("flow_modules/aiflows/FunSearchFlowModule","./cf_functions.py")
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
    funsearch_cfg["subflows_config"]["SamplerFlow"]["system_message_prompt_template"]["partial_variables"] = \
        {
            "evaluate_name": evaluate_function_name,
            "evolve_name": evolve_function_name,
            "artifacts_per_prompt": 2
        }
        
        
    return funsearch_cfg, dummy_solution 