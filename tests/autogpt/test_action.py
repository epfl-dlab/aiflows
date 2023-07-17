from flows.utils import logging

logging.set_verbosity_debug()

dependencies = [
    {"url": "FlowsEpfl/AutoGPTFlow_repo", "revision": "/Users/saibo/Development/Flow_dev/AutoGPTFlow_repo"},
    {"url": "FlowsEpfl/ReActFlow", "revision": "/Users/saibo/Development/Flow_dev/ReActFlow_repo"},
]
from flows import flow_verse
flow_verse.sync_dependencies(dependencies)

import os

from flow_modules.FlowsEpfl.AutoGPTFlow_repo import ActionFlow

if __name__ == "__main__":
    # python -m Flow_dev.WikipediaFlow.AgentFlow
    from flows.flow_launchers import FlowLauncher
    curr_flow = ActionFlow.instantiate_from_default_config()

    input_data = [
        {
        "id": 0,
        "command": "search",
        "command_args": {
            "search_term": "George Washington"
        }

    }]

    full_outputs, human_readable_outputs = FlowLauncher.launch(flow=curr_flow, data=input_data)

    print(human_readable_outputs)


