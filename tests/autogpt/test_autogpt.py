from flows.utils import logging

logging.set_verbosity_debug()

dependencies = [
    {"url": "FlowsEpfl/AutoGPTFlow_repo", "revision": "/Users/saibo/Development/Flow_dev/AutoGPTFlow_repo"},
    {"url": "FlowsEpfl/ReActFlow_repo", "revision": "/Users/saibo/Development/Flow_dev/ReActFlow_repo"},
]
from flows import flow_verse
flow_verse.sync_dependencies(dependencies)

import os

from flow_modules.FlowsEpfl.AutoGPTFlow_repo import AutoGPTFlow

if __name__ == "__main__":
    # python -m Flow_dev.WikipediaFlow.AgentFlow
    from flows.flow_launchers import FlowLauncher

    openai_key = os.environ.get("OPENAI_API_KEY")
    curr_flow = AutoGPTFlow.instantiate_from_default_config()

    print(curr_flow)

    input_data = [
        {
        "id": 0,
        "goal": "Find the answer of the question: How many people live in canada as of 2023?", # , save it in a text file.
        "memory_operation": "read",

    }]
    full_outputs, human_readable_outputs = FlowLauncher.launch(flow=curr_flow, data=input_data, api_keys={"openai": os.getenv("OPENAI_API_KEY")})

    print(human_readable_outputs)


