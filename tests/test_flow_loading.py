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


def test_loading_nested_flow() -> None:
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

    gen_flow_dict = {
        "_target_": "flows.base_flows.OpenAIChatAtomicFlow",
        "name": "gen_flow",
        "description": "gen_desc",
        "expected_inputs": ["input_0", "input_1"],
        "expected_outputs": ["gen_out"],
        "model_name": "gpt-model",
        "generation_parameters": {"temperature": 0.7},
        "system_message_prompt_template": sys_prompt,
        "human_message_prompt_template": hum_prompt
    }

    crit_flow_dict = {
        "_target_": "flows.base_flows.FixedReplyAtomicFlow",
        "name": "dummy_crit_name_fr",
        "description": "dummy_crit_desc_fr",
        "fixed_reply": "DUMMY CRITIC",
        "expected_outputs": ["query"]
    }

    first_flow_dict = {
        "_target_": "flows.base_flows.GeneratorCriticFlow",
        "name": "gen_crit_flow",
        "description": "gen_crit_desc",
        "expected_inputs": ["input_0", "input_1"],
        "expected_outputs": ["gen_crit_out"],
        "generator_flow": gen_flow_dict,
        "critic_flow": crit_flow_dict,
        "n_rounds": 2,
        "eoi_key": "eoi_key"
    }

    second_flow_dict = {
        "_target_": "flows.base_flows.FixedReplyAtomicFlow",
        "name": "dummy_name_fr",
        "description": "dummy_desc_fr",
        "fixed_reply": "dummy_fixed_reply",
        "expected_outputs": ["output_key"]
    }

    cfg = OmegaConf.create({
        "_target_": "flows.base_flows.SequentialFlow",
        "name": "dummy_name",
        "description": "dummy_desc",
        "expected_inputs": ["input_0", "input_1"],
        "expected_outputs": ["output_key"],
        "first_flow": first_flow_dict,
        "second_flow": second_flow_dict
    })

    nested_flow = instantiate_flow(cfg)
    assert isinstance(nested_flow, SequentialFlow)
    assert len(nested_flow.flows) == 2

    first_flow = nested_flow.flows["first_flow"]
    assert isinstance(first_flow, GeneratorCriticFlow)
    assert first_flow.name == "gen_crit_flow"
    assert first_flow.n_rounds == 2

    gen_flow = first_flow.flows["generator_flow"]
    assert isinstance(gen_flow, OpenAIChatAtomicFlow)
    assert gen_flow.generation_parameters["temperature"] == 0.7
    assert gen_flow.system_message_prompt_template.template == "You are a helpful assistant"

    crit_flow = first_flow.flows["critic_flow"]
    assert isinstance(crit_flow, FixedReplyAtomicFlow)
    assert crit_flow.fixed_reply == "DUMMY CRITIC"

    second_flow = nested_flow.flows["second_flow"]
    assert isinstance(second_flow, FixedReplyAtomicFlow)
    assert second_flow.fixed_reply == "dummy_fixed_reply"


if __name__ == "__main__":
    test_empty_loading()
