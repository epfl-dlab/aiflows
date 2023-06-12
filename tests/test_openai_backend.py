import langchain
import pytest
from langchain.chat_models import ChatOpenAI

from flows.base_flows import OpenAIChatAtomicFlow, Flow
from flows.messages import TaskMessage
from flows.messages.chat_message import ChatMessage
from tests.mocks import MockChatOpenAI, MockBrokenChatOpenAI, MockAnnotator
import time


def test_missing_keys():
    with pytest.raises(KeyError):
        OpenAIChatAtomicFlow()

    with pytest.raises(KeyError):
        OpenAIChatAtomicFlow(model_name="gpt-model")

    with pytest.raises(KeyError):
        OpenAIChatAtomicFlow(model_name="gpt-model", generation_parameters={})

    with pytest.raises(KeyError):
        OpenAIChatAtomicFlow(model_name="gpt-model", generation_parameters={}, system_message_prompt_template={})

def test_success(monkeypatch):
    monkeypatch.setattr(langchain.chat_models, "ChatOpenAI", MockChatOpenAI)
    monkeypatch.setattr(time, "sleep", lambda x: None)

    expected_out = ["answer"]
    expected_in =  ["input_0", "input_1"]
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
        "expected_inputs": expected_in,
        "expected_outputs": ["gen_out"],
        "model_name": "gpt-model",
        "generation_parameters": {"temperature": 0.7},
        "system_message_prompt_template": sys_prompt,
        "human_message_prompt_template": hum_prompt,
        "query_message_prompt_template": query_prompt,
        "response_annotators" : {"answer": {"_target_": "tests.mocks.MockAnnotator", "key": "answer"}}

    }

    openai_flow = OpenAIChatAtomicFlow(**gen_flow_dict)
    openai_flow = OpenAIChatAtomicFlow.instantiate(gen_flow_dict)
    assert openai_flow.expected_inputs_given_state() == expected_in


    answer_annotator = openai_flow._get_annotator_with_key("answer")
    assert answer_annotator is not None

    openai_flow.set_api_key("foo")

    task_message = openai_flow.package_task_message(openai_flow, "test", {"question": "What is your answer?"}, expected_out)
    output = openai_flow(task_message)
    assert "answer" in output.data

def test_state_update():
    expected_out = ["answer"]
    expected_in = ["input_0", "input_1"]
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
        "expected_inputs": expected_in,
        "expected_outputs": ["gen_out"],
        "model_name": "gpt-model",
        "generation_parameters": {"temperature": 0.7},
        "system_message_prompt_template": sys_prompt,
        "human_message_prompt_template": hum_prompt,
        "query_message_prompt_template": query_prompt,
        "response_annotators": {"answer": {"_target_": "tests.mocks.MockAnnotator", "key": "answer"}}

    }

    openai_flow = OpenAIChatAtomicFlow(**gen_flow_dict)
    assert len(openai_flow.flow_state["history"]) == 0
    openai_flow._update_state({"answer": "foo"}, [])
    assert len(openai_flow.flow_state["history"]) == 1

    msg = openai_flow.package_task_message(openai_flow, "test", {"question": "What is your answer?"}, expected_out)
    openai_flow._update_state(msg, [])
    assert len(openai_flow.flow_state["history"]) == 2
    assert openai_flow.flow_state["question"] == "What is your answer?"
    assert openai_flow._get_keys_from_state(["question"])["question"] == "What is your answer?"

    # can we recover a key from the class namespace
    assert openai_flow._get_keys_from_state(["name"])["name"] == "gen_flow"

    history_length_before = len(openai_flow.flow_state["history"])

    # the following should not update state, and therefore not log a message
    # history length stays unchanged
    # logs warning
    openai_flow._update_state({}, [])

    # continue on existing value
    openai_flow._update_state(msg, [])
    assert len(openai_flow.flow_state["history"]) == history_length_before
    assert openai_flow.flow_state["question"] == "What is your answer?"

    # the state has been updated, let's try to package an output message from it
    msg = openai_flow._package_output_message(openai_flow.flow_state, ["question"], [])
    assert msg.data["question"] == "What is your answer?"

    # the state has been updated, let's try to package an output message from it
    msg = openai_flow._package_output_message(openai_flow.flow_state, ["question"], [])
    assert msg.data["question"] == "What is your answer?"

    # trying to package an output message with missing keys produces an error
    msg = openai_flow._package_output_message(openai_flow.flow_state, ["question", "answer", "rudolph"], [])
    assert msg.error_message is not None


def test_failure(monkeypatch):
    monkeypatch.setattr(langchain.chat_models, "ChatOpenAI", MockBrokenChatOpenAI)
    monkeypatch.setattr(time, "sleep", lambda x: None)

    expected_out = ["answer"]
    expected_in = ["question"]
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
        "query_message_prompt_template": query_prompt,

    }

    openai_flow = OpenAIChatAtomicFlow(**gen_flow_dict)

    openai_flow.set_api_key("foo")

    task_message = openai_flow.package_task_message(openai_flow, "test", {"question": "What is your answer?"},
                                                    expected_out)

    # the following call raises an exception
    # expect it with pytest
    with pytest.raises(Exception):
        output = openai_flow(task_message)





def test_conv_init(monkeypatch):
    monkeypatch.setattr(langchain.chat_models, "ChatOpenAI", MockChatOpenAI)
    monkeypatch.setattr(time, "sleep", lambda x: None)

    expected_out = ["answer"]
    sys_prompt = {
        "_target_": "langchain.PromptTemplate",
        "template": "You are a helpful assistant",
        "input_variables": []
    }

    hum_prompt = {
        "_target_": "langchain.PromptTemplate",
        "template": "Please respond nicely  {query}",
        "input_variables": ["query"]
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
        "query_message_prompt_template": query_prompt,

    }

    openai_flow = OpenAIChatAtomicFlow(**gen_flow_dict)

    openai_flow.set_api_key("foo")

    task_message = openai_flow.package_task_message(openai_flow, "test", {"query": "What is your answer?"},
                                                    expected_out)


    _ = openai_flow(task_message)

    expected_inputs = openai_flow.expected_inputs_given_state()

    for key in expected_inputs:
        assert key in task_message.data.keys()
    _ = openai_flow(task_message)


def test_inspect_conversation(monkeypatch):
    monkeypatch.setattr(langchain.chat_models, "ChatOpenAI", MockChatOpenAI)
    monkeypatch.setattr(time, "sleep", lambda x: None)

    expected_out = ["answer"]
    sys_prompt = {
        "_target_": "langchain.PromptTemplate",
        "template": "You are a helpful assistant",
        "input_variables": []
    }

    hum_prompt = {
        "_target_": "langchain.PromptTemplate",
        "template": "Please respond nicely  {query}",
        "input_variables": ["query"]
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
        "query_message_prompt_template": query_prompt,

    }

    openai_flow = OpenAIChatAtomicFlow(**gen_flow_dict)

    openai_flow.set_api_key("foo")

    task_message = openai_flow.package_task_message(openai_flow, "test", {"query": "What is your answer?"},
                                                    expected_out)

    _ = openai_flow(task_message)

    openai_flow.get_conversation_messages()
    with pytest.raises(ValueError):
        openai_flow.get_conversation_messages("unknown message format")

    with pytest.raises(ValueError):
        message = ChatMessage(flow_run_id=openai_flow.flow_run_id, message_creator="unknown message creator")
        openai_flow.flow_state["history"].messages.append(message)
        openai_flow.get_conversation_messages(message_format="open_ai")


def test_add_demonstration(monkeypatch):
    monkeypatch.setattr(langchain.chat_models, "ChatOpenAI", MockChatOpenAI)
    monkeypatch.setattr(time, "sleep", lambda x: None)

    expected_out = ["answer"]
    sys_prompt = {
        "_target_": "langchain.PromptTemplate",
        "template": "You are a helpful assistant",
        "input_variables": []
    }

    hum_prompt = {
        "_target_": "langchain.PromptTemplate",
        "template": "Please respond nicely  {query}",
        "input_variables": ["query"]
    }

    query_prompt = {
        "_target_": "langchain.PromptTemplate",
        "template": "Bam, code {query}",
        "input_variables": ["query"]
    }

    demonstration_template={
        "_target_": "langchain.PromptTemplate",
        "template": "Bam, code {answer}",
        "input_variables": ["answer"]
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
        "query_message_prompt_template": query_prompt,
        "demonstrations_response_template": demonstration_template,
        "demonstrations": [{"query":"What is your answer?", "answer": "answer"}]
    }

    openai_flow = OpenAIChatAtomicFlow(**gen_flow_dict)

    openai_flow.set_api_key("foo")

    task_message = openai_flow.package_task_message(openai_flow, "test", {"query": "What is your answer?"},
                                                    expected_out)

    output = openai_flow(task_message)
    print(output)


def test_response_annotator_wrong_key(monkeypatch):
    monkeypatch.setattr(langchain.chat_models, "ChatOpenAI", MockChatOpenAI)
    monkeypatch.setattr(time, "sleep", lambda x: None)

    expected_out = ["answer"]
    expected_in = ["question"]
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
        "query_message_prompt_template": query_prompt,
        "response_annotators": {"answer": {"_target_": "tests.mocks.MockAnnotator", "key": "wrong key"}}

    }

    openai_flow = OpenAIChatAtomicFlow(**gen_flow_dict)

    answer_annotator = openai_flow._get_annotator_with_key("answer")
    assert answer_annotator is None
