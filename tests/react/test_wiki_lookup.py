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
        "lookup_term": "President",
        "wiki_content": "President of the United States",
    },
        {
        "id": 1,
        "lookup_term": "President of India",
        "wiki_content": "XXX",
    },
        ]

    full_outputs, human_readable_outputs = FlowLauncher.launch(flow=curr_flow, data=input_data)
    assert human_readable_outputs[0]["observation"] == "(Result 1/1) President of the United States"

    assert human_readable_outputs[1]["observation"] == "No Results"