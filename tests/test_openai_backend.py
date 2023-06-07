import langchain
from langchain.chat_models import ChatOpenAI

from src.flows import OpenAIChatAtomicFlow
from tests.mocks import MockChatOpenAI, MockTemplate


def test_openai_backend(monkeypatch):
    monkeypatch.setattr(langchain.chat_models, "ChatOpenAI", MockChatOpenAI)

    openai_flow = OpenAIChatAtomicFlow(
        name="openai",
        description="openai",
        expected_inputs=[], expected_outputs=["response"],
        model_name="doesn't exist",
        generation_parameters={},
        system_message_prompt_template=MockTemplate(""),
        human_message_prompt_template=MockTemplate(""),
        query_message_prompt_template=MockTemplate(""),
        wait_time_between_retries=0,
    )
    openai_flow.initialize()
    openai_flow.set_api_key("foo")

    output = openai_flow()

    print(output)
