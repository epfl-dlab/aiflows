from flows.utils import logging

logging.set_verbosity_debug()

dependencies = [
    {"url": "FlowsEpfl/ReActFlowModule", "revision": "/Users/saibo/Development/Flow_dev/ReActFlowModule"},
]
from flows import flow_verse
flow_verse.sync_dependencies(dependencies)

import os

from flow_modules.FlowsEpfl.ReActFlowModule import WikiSearchAtomicFlow
from flows.flow_launchers import FlowLauncher

if __name__ == '__main__':
    # python -m Flow_dev.WikipediaFlow.WikiLookupAtomicFlow
    from flows.flow_launchers import FlowLauncher
    curr_flow = WikiSearchAtomicFlow.instantiate_from_default_config()

    input_data = [
        {
        "id": 0,
        "search_term": "President",
        "wiki_content": "President of the United States",
    },
        {
        "id": 1,
        "search_term": "President of India",
        "wiki_content": "XXX",
    },
        ]

    full_outputs, human_readable_outputs = FlowLauncher.launch(flow=curr_flow, data=input_data)
    assert human_readable_outputs[0]["observation"].startswith("Could not find [President]") and \
              human_readable_outputs[0]["wiki_content"] is None
    assert human_readable_outputs[1]["observation"].startswith("The president of India (IAST: Bhārat kē Rāṣṭrapati)") and \
                human_readable_outputs[1]["wiki_content"] is not None