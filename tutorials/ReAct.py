import os
from flows.flow_launchers import FlowLauncher
from flows import flow_verse

dependencies = [
    {"url": "FlowsEpfl/ReActFlowModule", "revision": "/Users/josifosk/Documents/PhD/ReActFlowModule"},
]
flow_verse.sync_dependencies(dependencies)

from FlowsEpfl.ReActFlowModule import ReActFlow

curr_flow = ReActFlow.instantiate_from_default_config()

input_data = [
    {
        "id": 0,
        "question": "What is the birth date of the first president of the United States ?",
    },
    #     {
    #     "id": 1,
    #         "question": "What is thee father's birth date of the first president of the United States ?",
    # },
    #     {"id": 2,
    #         "question": "What is the PhD theis title of the first female  president of EPFL in Switzerland ?",
    # },
]
print(curr_flow)
# sys.exit()


full_outputs, human_readable_outputs = FlowLauncher.launch(flow=curr_flow,
                                                           data=input_data,
                                                           api_keys={"openai": os.getenv("OPENAI_API_KEY")})
import json

print(json.dumps(human_readable_outputs, indent=4))
# print(human_readable_outputs)