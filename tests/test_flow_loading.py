import langchain

from flows.base_flows import SequentialFlow, GeneratorCriticFlow, FixedReplyAtomicFlow, OpenAIChatAtomicFlow
from flows.utils import instantiate_flow
from omegaconf import OmegaConf
from hydra.errors import InstantiationException
import pytest
import hydra


def test_empty_loading() -> None:
    cfg = OmegaConf.create()
    assert instantiate_flow(cfg) == {}


def test_example_loading() -> None:
    cfg = OmegaConf.create({
        "_target_": "flows.base_flows.FixedReplyAtomicFlow",
        "name": "dummy_name",
        "description": "dummy_desc",
        "fixed_reply": "dummy_fixed_reply"
    })

    flow = instantiate_flow(cfg)
    assert flow.name == "dummy_name"
    assert flow.verbose  # test that defaults are set
    answer = flow.run(input_data=None, expected_outputs=["answer"])
    assert answer["answer"] == "dummy_fixed_reply"


def test_openai_atomic_loading() -> None:
    sys_prompt = {
        "_target_": "langchain.PromptTemplate",
        "template": "You are a helpful assistant",
        "input_variables": []
    }

    hum_prompt = {
        "_target_": "langchain.PromptTemplate",
        "template": "Please respond nicely",
        "input_variables": []
    }

    query_prompt = {
        "_target_": "langchain.PromptTemplate",
        "template": "Bam, code",
        "input_variables": []
    }

    gen_flow_dict = {
        "_target_": "flows.base_flows.OpenAIChatAtomicFlow",
        "name": "gen_flow",
        "description": "gen_desc",
        "expected_inputs": ["input_0", "input_1"],
        "expected_outputs": ["gen_out"],
        "model_name": "gpt-model",
        "generation_parameters": {"temperature": 0.7},
        "system_message_prompt_template": sys_prompt,
        "human_message_prompt_template": hum_prompt,
        "query_message_prompt_template": query_prompt
    }

    flow = OpenAIChatAtomicFlow(**gen_flow_dict)

    assert flow.name == "gen_flow"
    assert flow.verbose  # test that defaults are set


def test_loading_wrong_inputs() -> None:
    cfg = OmegaConf.create({
        "_target_": "flows.base_flows.FixedReplyAtomicFlow",
        "name": "dummy_name",
        "description": "dummy_desc",
        "fixed_reply": "dummy_fixed_reply",
        "faulty_param": True
    })

    instantiate_flow(cfg)

