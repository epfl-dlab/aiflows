from flows.utils import logging
from flows.base_flows import CircularFlow

logging.set_verbosity_debug()

dependencies = [
    {"url": "FlowsEpfl/ReActFlowModule", "revision": "/Users/saibo/Development/Flow_dev/ReActFlowModule"},
]
from flows import flow_verse

flow_verse.sync_dependencies(dependencies)

import os

from flow_modules.FlowsEpfl.ReActFlowModule import ReActFlow, AgentAtomicFlow, ActionFlow
from flows.flow_launchers import FlowLauncher
from flows.data_transformations import KeyRename


if __name__ == "__main__":
    openai_key = os.environ.get("OPENAI_API_KEY")
    react_flow = CircularFlow.instantiate_from_default_config(
        overrides={"output_keys": ["answer", "_status"], "run_output_keys": ["observation", "_status"]}
    )

    agent_flow = AgentAtomicFlow.instantiate_from_default_config(overrides={"verbose": False, "api_key": openai_key})
    action_flow = ActionFlow.instantiate_from_default_config()

    react_flow.add_subflow(agent_flow)
    react_flow.add_subflow(action_flow)

    key_rename_dt = KeyRename(old_key2new_key={"observation": "answer"})

    react_flow.add_output_data_transformation(key_rename_dt)

    print(react_flow)

    input_data = {
        "id": 0,
        "question": "What is the birth date of the first president of the United States ?",
    }
    #     {
    #     "id": 1,
    #         "question": "What is the father's birth date of the first president of the United States ?",
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
    assert (
        output_message.get_output_data()["answer"] == "February 22, 1732"
    ), f"output_message.get_output_data()['answer'] = {output_message.get_output_data()['answer']}"
    assert (
        output_message.get_output_data()["_status"] == "finished"
    ), f"output_message.get_output_data()['_status'] = {output_message.get_output_data()['_status']}"

    # input_data = {
    #         "id": 1,
    #         "question": "What is the birth date of the father of the first president of the United States ?",
    #     }
    #
    #
    #
    # # sys.exit()
    # react_flow.reset(full_reset=True, recursive=True)
    # input_message = react_flow.package_input_message(input_data, api_keys={"openai": openai_key})
    # output_message = react_flow(input_message)
    # assert output_message.get_output_data()["_status"] == "finished"
    #
    #
    # input_data = {
    #         "id": 2,
    #     "question": "What is the PhD theis title of the first female president of EPFL in Switzerland ?"
    # }
    # react_flow.reset(full_reset=True, recursive=True)
    # input_message = react_flow.package_input_message(input_data, api_keys={"openai": openai_key})
    #
    # output_message = react_flow(input_message)
    #
    # assert output_message.get_output_data()["_status"] == "unfinished"
