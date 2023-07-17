from flows.utils import logging

logging.set_verbosity_debug()

dependencies = [
    {"url": "FlowsEpfl/ReActFlow", "revision": "/Users/saibo/Development/Flow_dev/ReActFlow"},
]
from flows import flow_verse
flow_verse.sync_dependencies(dependencies)

import os

from flow_modules.FlowsEpfl.ReActFlow import ReActFlow
from flows.flow_launchers import FlowLauncher


if __name__ == "__main__":
    openai_key = os.environ.get("OPENAI_API_KEY")
    react_flow = ReActFlow.instantiate_from_default_config()


    input_data = {
            "id": 0,
            "question": "What is the birth date of the first president of the United States ?",
        }
        #     {
        #     "id": 1,
        #         "question": "What is thee father's birth date of the first president of the United States ?",
        # },
        #
        # {"id": 2,
        #  "question": "What is the PhD theis title of the first female  president of EPFL in Switzerland ?",
        #
        #  },
    # ]
    # print(react_flow)

    input_message = react_flow.package_input_message(input_data, api_keys={"openai": openai_key})
    # sys.exit()
    output_message = react_flow(input_message)