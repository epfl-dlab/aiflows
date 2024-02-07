import os
from multiprocessing import Process, Queue
from aiflows import flow_verse
from aiflows.backends.api_info import ApiInfo
import os
from aiflows import logging
from aiflows.utils.general_helpers import read_yaml_file, quick_load
from aiflows.base_flows import AtomicFlow
from aiflows.flow_launchers import FlowLauncher
logging.set_verbosity_debug() 

def process(queue, cfg_path, data):
    
    cfg = read_yaml_file(cfg_path)
    
    flow_with_interfaces = {
        "flow": AtomicFlow.instantiate_from_default_config(**cfg)
    }
    
    _, outputs = FlowLauncher.launch(
        flow_with_interfaces=flow_with_interfaces,
        data=data,
        path_to_output_file=None,
    )

    flow_output_data = outputs[0]
    queue.put(flow_output_data)

if __name__ == "__main__":
    # Define the data for each process
    
    countries = ["Switzerland", "Croatia", "France", "Germany",
                 "Italy", "Spain"]
    
    datas = [{"id": i, "query": f"What is the Capital of {country}?"} for i, country in enumerate(countries)]
    
    root_dir = "."
    cfg_path = os.path.join(root_dir, "proxy-demo.yaml")
    
    # Create a queue for inter-process communication
    queue = Queue()
    
    # Create processes
    processes = [Process(target=process, args=(queue, cfg_path, data)) for data in datas]
    
    for p in processes:
        p.start() 

    for p in processes:
        p.join()    
    
    for p in processes:
        data = queue.get()
        print(data)
    