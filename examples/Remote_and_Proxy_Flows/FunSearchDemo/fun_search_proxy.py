from aiflows import flow_verse
from aiflows.backends.api_info import ApiInfo
import os
from aiflows import logging
from aiflows.utils.general_helpers import read_yaml_file, quick_load
from aiflows.base_flows import AtomicFlow
from aiflows.flow_launchers import FlowLauncher
logging.set_verbosity_debug()
from Loader import Loader

if __name__ == "__main__":
        
    root_dir = "."
    cfg_path = os.path.join(root_dir, "fun_search_proxy.yaml")
    
    cfg = read_yaml_file(cfg_path)
    
    
    evaluate_function_file_path: str = "./functions.py"
    evaluate_function_name: str = "evaluate"
    loader = Loader(file_path = evaluate_function_file_path, target_name = evaluate_function_name)
    evaluate_function: str= loader.load_target()
    evaluate_file_full_content = loader.load_full_file()
    
    cfg["subflows_config"]["ProgramDBFlow"]["evaluate_function"] = evaluate_function
    cfg["subflows_config"]["ProgramDBFlow"]["evaluate_file_full_content"] = evaluate_file_full_content
    cfg["subflows_config"]["EvaluatorFlow"]["py_file"] = evaluate_file_full_content
    cfg["subflows_config"]["SamplerFlow"]["backend"]["api_infos"] = \
        [ApiInfo(backend_used="openai", api_key=os.getenv("OPENAI_API_KEY"))]
    
    
    artifact_file_path ="functions.py"
    artifact_to_evolve_name = "priority_function"
    artifact_to_evolve: str= Loader(file_path = artifact_file_path,target_name = artifact_to_evolve_name).load_target()
    # ~~~ Instantiate the Flow ~~~
    flow_with_interfaces = {
        "flow": AtomicFlow.instantiate_from_default_config(**cfg)
    }
     # ~~~ Get the data ~~~
    data = {
        "id": 0,
        "artifact": artifact_to_evolve,
    }
    print("launhing...")
    _, outputs = FlowLauncher.launch(
        flow_with_interfaces=flow_with_interfaces,
        data=data,
        path_to_output_file=None,
    )
    
   
    # ~~~ Print the output ~~~
    flow_output_data = outputs[0]
    print(flow_output_data)