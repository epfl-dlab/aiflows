import os
from typing import Dict, Any, List

import arxiv
import fitz
import hydra.utils
import langchain
import tqdm
from arxiv import SortCriterion, SortOrder, ArxivError
from copy import deepcopy

from langchain import PromptTemplate

from flows.base_flows import AtomicFlow, SequentialFlow, OpenAIChatAtomicFlow
from langchain.schema import Document
from tutorials.DailyArxivSummarizerFlow import ArxivDocumentTransform, ArxivAPIAtomicFlow

from flows.utils.caching_utils import flow_run_cache

DEFAULT_HUMAN_PROMPT = {
        "_target_": "langchain.PromptTemplate",
        "template": "Please provide your question: ",
        "input_variables": [],
    }


class HumanInputAtomicFlow(AtomicFlow):
    human_prompt_template: PromptTemplate

    def __init__(self, **kwargs):
        if "human_prompt_template" not in kwargs:
            kwargs["human_prompt_template"] = DEFAULT_HUMAN_PROMPT

        super().__init__(**kwargs)
        self._instantiate()

    def _instantiate(self):
        self.human_prompt_template = hydra.utils.instantiate(self.flow_config["human_prompt_template"], _convert_="partial")

    def expected_inputs_given_state(self):
        return self.human_prompt_template.input_variables

    def _get_input_message(self, input_data: Dict[str, Any]):
        template_kwargs = {}
        for input_variable in self.human_prompt_template.input_variables:
            template_kwargs[input_variable] = input_data[input_variable]

        return self.human_prompt_template.format(**template_kwargs)

    def run(self, input_data: Dict[str, Any], output_keys: List[str]) -> Dict[str, Any]:
        # sys_prompt = input_data["explanation_for_human_input"]
        user_input = input(self._get_input_message(input_data))
        return {output_keys[0]: user_input}


if __name__ == "__main__":
    field = "stat.ML"
    query = f"cat:{field}"
    max_results = 5

    # ~~~ ArxivAPIAtomicFlow ~~~
    arxiv_flow = ArxivAPIAtomicFlow(
        name="ArxivAPIAtomicFlow",
        description="Retrieves last n arxiv paper from a given field",
        sort_by=SortCriterion.SubmittedDate,
        expected_inputs=["field", "max_results"],
        output_keys=["arxiv_outputs"],
        get_content=False,
        get_basic_content=True
    )

    # ~~~ ArxivDocumentTransform ~~~
    arxiv_transform_flow = ArxivDocumentTransform(
        name="ArxivDocumentTransform",
        description="Takes the output of an ArxivAPIAtomicFlow and parses it into a string",
        expected_inputs=["arxiv_outputs"],
        output_keys=["paper_descriptions"]
    )

    # ~~~ HumanInputAtomicFlow ~~~
    human_prompt_template = {
        "_target_": "langchain.PromptTemplate",
        "template": "Ask me a question that can be answered from the abstracts of "
                    "recently uploaded papers on arXiv: ",
        "input_variables": [],
        "template_format": "jinja2"
    }
    human_input_flow = HumanInputAtomicFlow(
        name="HumanInputAtomicFlow",
        description="Asks the user for a question",
        expected_inputs=["sys_prompt"],
        output_keys=["human_query"],
        human_prompt_template=human_prompt_template
    )

    # ~~~ SummarizerFlow ~~~
    sys_prompt = {
        "_target_": "langchain.PromptTemplate",
        "template": "You are an expert in the field {{field}}. A fellow researcher is asking you a question. "
                    "After downloading all recently published arxiv"
                    "papers in the field, and reading their abstracts, you answer the question. "
                    "Your answer is clearly written and helpful.",
        "input_variables": ["field"],
        "template_format": "jinja2"
    }
    query_prompt = {
        "_target_": "langchain.PromptTemplate",
        "template": "\nHere are the arxiv abstracts:\n\n{{paper_descriptions}}. And this is the question you should respond to: {{human_query}}.",
        "input_variables": ["paper_descriptions", "human_query"],
        "template_format": "jinja2",
    }
    hum_prompt = deepcopy(query_prompt)

    QA_flow = OpenAIChatAtomicFlow(
        name="SummarizeArxiv",
        description="summarizes several arxiv paper",
        model_name="gpt-3.5-turbo",
        generation_parameters={},
        expected_inputs=["field", "paper_descriptions", "human_query"],
        output_keys=["ai_answer"],
        system_message_prompt_template=sys_prompt,
        human_message_prompt_template=hum_prompt,
        query_message_prompt_template=query_prompt
    )

    # ~~~ DailyArxivSummarizer ~~~
    arxiv_qa_flow = SequentialFlow(
        name="summarizer arxiv",
        description="summarizes arxiv",
        expected_inputs=["field", "max_results", "api_key"],
        output_keys=["summary"],
        flows={
            "arxiv_flow": arxiv_flow,
            "arxiv_transform_flow": arxiv_transform_flow,
            "human_input": human_input_flow,
            "QA_flow": QA_flow
        }
    )
    # explanation_for_human_input = "Ask me a question that can be answered from the abstracts of recently uploaded papers on arXiv: "
    input_message = arxiv_qa_flow.package_task_message(
        recipient_flow=arxiv_qa_flow,
        task_name="summarize arxiv",
        task_data={
            # "explanation_for_human_input": explanation_for_human_input,
            "field": field,
            "query": query,
            "max_results": max_results,
            "api_key": os.getenv("OPENAI_API_KEY")},
        output_keys=["ai_answer"]
    )

    answer = arxiv_qa_flow(input_message)
    print(answer.data)
