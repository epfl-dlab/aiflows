from flows.utils import logging

logging.set_verbosity_debug()

dependencies = [
    {"url": "FlowsEpfl/AutoGPTFlowModule", "revision": "main"},
]
from flows import flow_verse

flow_verse.sync_dependencies(dependencies)

import os

from flow_modules.FlowsEpfl.AutoGPTFlowModule import AgentAtomicFlow

if __name__ == "__main__":
    # python -m Flow_dev.WikipediaFlow.AgentFlow
    from flows.flow_launchers import FlowLauncher

    openai_key = os.environ.get("OPENAI_API_KEY")
    curr_flow = AgentAtomicFlow.instantiate_from_default_config(overrides={"verbose": False, "api_key": openai_key})

    input_data = [
        {
            "id": 0,
            "goal": "Find the answer of the question: How many people live in canada as of 2023?, save it in a text file.",
        }
    ]

    full_outputs, human_readable_outputs = FlowLauncher.launch(
        flow=curr_flow, data=input_data, api_keys={"openai": os.getenv("OPENAI_API_KEY")}
    )

    print(human_readable_outputs)
    print(f'previous message: {len(curr_flow.flow_state["previous_messages"])}')

    #
    # input_data = [
    #     {
    #     "id": 0,
    #         "history": ["search[George Washington]"],
    #     },
    #     ]
    #
    # full_outputs, human_readable_outputs = FlowLauncher.launch(flow=curr_flow, data=input_data, api_keys={"openai": os.getenv("OPENAI_API_KEY")})

    """
    Needs to
    class FlowLauncher(ABC):
    @staticmethod
    def launch(flow: Flow,
        for sample in data:
            flow.reset(full_reset=False, recursive=True)  # change from True to False of full_reset to make this work

    """
    print(human_readable_outputs)
    print(f'previous message: {len(curr_flow.flow_state["previous_messages"])}')
