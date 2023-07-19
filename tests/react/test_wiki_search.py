from flows.utils import logging

logging.set_verbosity_debug()

dependencies = [
    {"url": "FlowsEpfl/ReActFlow_repo", "revision": "/Users/saibo/Development/Flow_dev/ReActFlow_repo"},
]
from flows import flow_verse
flow_verse.sync_dependencies(dependencies)

import os

from flow_modules.FlowsEpfl.ReActFlow_repo import WikiLookupAtomicFlow
from flows.flow_launchers import FlowLauncher

if __name__ == '__main__':
    # python -m Flow_dev.WikipediaFlow.WikiLookupAtomicFlow
    from flows.flow_launchers import FlowLauncher
    curr_flow = WikiLookupAtomicFlow.instantiate_from_default_config()

    input_data = [
        {
        "id": 0,
        "term": "President",
        "wiki_content": "President of the United States",
        "lookup_idx": 0
    },
        {
        "id": 1,
        "term": "President",
        "wiki_content": "XXX",
        "lookup_idx": 0
    },
        ]

    full_outputs, human_readable_outputs = FlowLauncher.launch(flow=curr_flow, data=input_data)

    print(human_readable_outputs)

    error_input_data ={
        "id": 2,
        "term": "President",
        "wiki_content": None,
        "lookup_idx": 0
    }

    try:
        full_outputs, human_readable_outputs = FlowLauncher.launch(flow=curr_flow, data=error_input_data)
    except ValueError as e:
        print(e)