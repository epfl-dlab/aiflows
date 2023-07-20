from flows.utils import logging

logging.set_verbosity_debug()

dependencies = [
    {"url": "FlowsEpfl/ReActModule", "revision": "/Users/saibo/Development/Flow_dev/ReActModule"},
]
from flows import flow_verse
flow_verse.sync_dependencies(dependencies)

import os

from flow_modules.FlowsEpfl.ReActModule import ActionFlow

if __name__ == "__main__":
    # python -m Flow_dev.WikipediaFlow.ActionFlow
    from flows.flow_launchers import FlowLauncher

    curr_flow = ActionFlow.instantiate_from_default_config()

    input_data = [
        {
            "id": 2,
            "command": "finish",
            "argument1": "George Washington ",

        }
    ]

    full_outputs, human_readable_outputs = FlowLauncher.launch(flow=curr_flow, data=input_data)

    print(human_readable_outputs)