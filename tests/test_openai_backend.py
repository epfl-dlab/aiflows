import langchain
from langchain.chat_models import ChatOpenAI

from src.flows import OpenAIChatAtomicFlow
from src.messages import TaskMessage
from tests.mocks import MockChatOpenAI


def test_openai_backend(monkeypatch):
    monkeypatch.setattr(langchain.chat_models, "ChatOpenAI", MockChatOpenAI)

    expected_out = ["answer"]
    expected_in = ["question"]

    system_message_prompt_template = langchain.PromptTemplate(
        template="You are an assistant",
        input_variables=[]
    )

    human_message_prompt_template = langchain.PromptTemplate(
        template="{{query}}",
        input_variables=["query"],
        template_format="jinja2"
    )

    query_message_prompt_template = langchain.PromptTemplate(
        template="Here is my question: {{question}}",
        input_variables=["question"],
        template_format="jinja2"
    )

    openai_flow = OpenAIChatAtomicFlow(
        name="openai",
        description="openai",
        model_name="doesn't exist",
        expected_outputs=expected_out,
        expected_inputs=expected_in,
        generation_parameters={},
        system_message_prompt_template=system_message_prompt_template,
        human_message_prompt_template=human_message_prompt_template,
        query_message_prompt_template=query_message_prompt_template,
        wait_time_between_retries=0,
    )

    openai_flow.initialize()
    openai_flow.set_api_key("foo")

    task_message = TaskMessage(
        expected_output_keys=expected_out,
        target_flow_run_id=openai_flow.state["flow_run_id"],
        message_creator="task",
        parent_message_ids=[],
        flow_runner="task",
        flow_run_id="00",
        data={"question": "What is your answer?"},
    )
    output = openai_flow(task_message)
    assert "answer" in output.data
