import langchain

from flows.base_flows import SequentialFlow, GeneratorCriticFlow, FixedReplyAtomicFlow, OpenAIChatAtomicFlow
from flows.utils import instantiate_flow
from omegaconf import OmegaConf
from hydra.errors import InstantiationException
import pytest
import hydra


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

    query_prompt = {
        "_target_": "langchain.PromptTemplate",
        "template": "Bam, code",
        "input_variables": []
    }

    gen_flow_dict = {
        "_target_": "flows.base_flows.OpenAIChatAtomicFlow",
        "name": "gen_flow",
        "description": "gen_desc",
        "expected_inputs": [],
        "output_keys": ["gen_out"],
        "model_name": "gpt-model",
        "generation_parameters": {"temperature": 0.7},
        "system_message_prompt_template": sys_prompt,
        "human_message_prompt_template": hum_prompt,
        "query_message_prompt_template": query_prompt,
    }

    openai_flow = OpenAIChatAtomicFlow(**gen_flow_dict)

    crit_flow_dict = {
        "_target_": "flows.base_flows.FixedReplyAtomicFlow",
        "name": "dummy_crit_name_fr",
        "description": "dummy_crit_desc_fr",
        "fixed_reply": "DUMMY CRITIC",
        "output_keys": ["query"]
    }

    critic_flow = FixedReplyAtomicFlow(**crit_flow_dict)

    first_flow_dict = {
        "_target_": "flows.base_flows.GeneratorCriticFlow",
        "name": "gen_crit_flow",
        "description": "gen_crit_desc",
        "expected_inputs": ["input_0", "input_1"],
        "output_keys": ["gen_crit_out"],
        "flows": {"generator_flow": openai_flow, "critic_flow": critic_flow},
        "n_rounds": 2,
        "eoi_key": "eoi_key"
    }

    gen_critic_flow = GeneratorCriticFlow(**first_flow_dict)

    second_flow_dict = {
        "_target_": "flows.base_flows.FixedReplyAtomicFlow",
        "name": "dummy_name_fr",
        "description": "dummy_desc_fr",
        "fixed_reply": "dummy_fixed_reply",
        "output_keys": ["output_key"]
    }

    second_flow = FixedReplyAtomicFlow(**second_flow_dict)

    sequential_flow_config = {
        "_target_": "flows.base_flows.SequentialFlow",
        "name": "dummy_name",
        "description": "dummy_desc",
        "expected_inputs": ["input_0", "input_1"],
        "output_keys": ["output_key"],
        "flows": [gen_critic_flow, second_flow]
    }

    nested_flow = SequentialFlow(**sequential_flow_config)

    assert isinstance(nested_flow, SequentialFlow)
    assert len(nested_flow.flows) == 2

    first_flow = nested_flow.flows[0]
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

    second_flow = nested_flow.flows[1]
    assert isinstance(second_flow, FixedReplyAtomicFlow)
    assert second_flow.fixed_reply == "dummy_fixed_reply"
