import pytest

from langchain.chat_models import ChatOpenAI
import langchain
from src.mockme.randomizer import Randomizer
from src.flows import OpenAIChatAtomicFlow
from tests.MockOpenAI import MockChatOpenAI, MockResponse


def test_numpy_random(monkeypatch):

    monkeypatch.setattr(np.random, "rand", lambda : 5)

    r = Randomizer()
    print(r.get())

    print("done")

def test_openai_backend(monkeypatch):

        monkeypatch.setattr(ChatOpenAI, "__call__", MockChatOpenAI.__call__)
        monkeypatch.setattr(ChatOpenAI, "__init__", MockChatOpenAI.__init__)

        chat = ChatOpenAI()

        print(chat("hello"))

        print("done")

def test_openai_backend_v2(monkeypatch):
    monkeypatch.setattr(langchain.chat_models, "ChatOpenAI", MockChatOpenAI)

    chat = langchain.chat_models.ChatOpenAI()
    print(chat("hello"))

class MockTemplate:
    def __init__(self, content):
        self.content = content
        self.input_variables=[]
    def format(self, *args, **kwargs):
        return self.content

    def to_string(self, *args, **kwargs):
        return self.content

def test_openai_backend_v3(monkeypatch):
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