from aiflows import flow_verse
from aiflows.backends.api_info import ApiInfo
import os
from aiflows import logging
from aiflows.utils.general_helpers import read_yaml_file, quick_load
from aiflows.base_flows import AtomicFlow
from aiflows.flow_launchers import FlowLauncher
logging.set_verbosity_debug() 

if __name__ == "__main__":
    api_information = [
        ApiInfo(backend_used="openai", api_key=os.getenv("OPENAI_API_KEY"))
    ]
    
    
    root_dir = "."
    cfg_path = os.path.join(root_dir, "proxy-demo.yaml")
    cfg = read_yaml_file(cfg_path)
    # ~~~ Instantiate the Flow ~~~
    flow_with_interfaces = {
        "flow": AtomicFlow.instantiate_from_default_config(**cfg)
    }

     # ~~~ Get the data ~~~
    data = {
        "id": 0,
        "query": "Where is the capital of croatia ?",
    }

    _, outputs = FlowLauncher.launch(
        flow_with_interfaces=flow_with_interfaces,
        data=data,
        path_to_output_file=None,
    )
    
   
    # ~~~ Print the output ~~~
    flow_output_data = outputs[0]
    print(flow_output_data)