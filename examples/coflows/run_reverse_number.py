import argparse
import os

from aiflows.utils import serve_utils
from aiflows.utils.general_helpers import read_yaml_file
from aiflows.messages import InputMessage

def parse_args():
    parser = argparse.ArgumentParser(description="CoFlows Demo program")

    env_addr = os.getenv("COLINK_CORE_ADDR")
    env_jwt = os.getenv("COLINK_JWT")

    parser.add_argument(
        "--addr",
        type=str,
        default=env_addr,
        required=env_addr is None,
        help="CoLink server address.",
    )
    parser.add_argument(
        "--jwt",
        type=str,
        default=env_jwt,
        required=env_jwt is None,
        help="Your JWT issued by the CoLink server.",
    )

    args = parser.parse_args()
    return vars(args)


FLOW_MODULES_PATH = "./"

if __name__ == "__main__":
    args = parse_args()
    cl = serve_utils.start_colink_component("Reverse Number Demo", args)

    # ~~~ Serve ReverseNumberAtomic ~~~
    reverse_number_atomic_default_config_path = os.path.join(
        FLOW_MODULES_PATH, "ReverseNumberFlowModule/ReverseNumberAtomicFlow.yaml"
    )
    reverse_number_atomic_default_config = read_yaml_file(
        reverse_number_atomic_default_config_path
    )
    serve_utils.serve_flow(
        cl=cl,
        flow_type="ReverseNumberAtomicFlow_served",
        default_config=reverse_number_atomic_default_config,
        default_state=None,
        default_dispatch_point="coflows_dispatch",
    )

    # ~~~ Serve ReverseNumberSequential ~~~
    reverse_number_sequential_default_config_path = os.path.join(
        FLOW_MODULES_PATH, "ReverseNumberFlowModule/ReverseNumberSequentialFlow.yaml"
    )
    reverse_number_sequential_default_config = read_yaml_file(
        reverse_number_sequential_default_config_path
    )
    serve_utils.serve_flow(
        cl=cl,
        flow_type="ReverseNumberSequentialFlow_served",
        default_config=reverse_number_sequential_default_config,
        default_state=None,
        default_dispatch_point="coflows_dispatch",
    )

    # ~~~ Mount ReverseNumberSequential --> will recursively mount two ReverseNumberAtomic flows ~~~
    config_overrides = None
    proxy_flow = serve_utils.recursive_mount(
        cl=cl,
        client_id="local",
        flow_type="ReverseNumberSequentialFlow_served",
        config_overrides=config_overrides,
        initial_state=None,
        dispatch_point_override=None,
    )

    print("Pushing to...", proxy_flow)

    
    input_data = {"id": 0, "number": 1234}
    
    input_message = InputMessage(
        data_dict= input_data,
        src_flow="Coflow team",
        dst_flow=proxy_flow,
    )
    
    print(proxy_flow.ask(input_message).get())
