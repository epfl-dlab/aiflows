import os
from typing import Dict, Any, List

import arxiv
import fitz
import langchain
import tqdm
from arxiv import SortCriterion, SortOrder, ArxivError

from flows.base_flows import AtomicFlow, SequentialFlow, OpenAIChatAtomicFlow
from langchain.schema import Document

from flows.utils.caching_utils import flow_run_cache


class ArxivDocumentTransform(AtomicFlow):

    @staticmethod
    def _dict_to_string(document: Dict):
        doc_str = ""
        for key, value in document.items():
            doc_str += f"{key}: {value}\n"
        return doc_str + "\n"

    @staticmethod
    def _document_to_string(document: Document):
        doc_str = ""
        if document.metadata:
            doc_str = "~~~ Metadata ~~~\n"
            for key, value in document.metadata.items():
                doc_str += f"{key}: {value}\n"
        if document.page_content:
            doc_str += f"\n\n ~~~ Content ~~~\n{document.page_content}\n\n"
        return doc_str

    @flow_run_cache()
    def run(self, input_data: Dict[str, Any], expected_outputs: List[str]) -> Dict[str, Any]:
        input_key = self.expected_inputs[0]
        documents = input_data[input_key]

        str_format = ""
        for doc in documents:
            if type(doc) is Document:
                str_format += self._document_to_string(doc)
            else:
                str_format += self._dict_to_string(doc)

        return {expected_outputs[0]: str_format}


class ArxivAPIAtomicFlow(AtomicFlow):
    def __init__(
            self,
            max_results: int = 300,
            sort_by: SortCriterion = SortCriterion.Relevance,
            # possible values are "lastUpdatedDate", and "submittedDate"
            sort_order: SortOrder = SortOrder.Descending,  # other possible value: "ascending"
            get_content: bool = True,
            get_basic_content: bool = False,
            **kwargs
    ):
        super().__init__(
            max_results=max_results,
            sort_by=sort_by,
            sort_order=sort_order,
            get_content=get_content,
            get_basic_content=get_basic_content,
            **kwargs
        )

    def expected_inputs_given_state(self):
        return ["query", "max_results", "sort_by", "sort_order", "get_content", "get_only_abstract"]

    def _read_value(self, input_data: Dict[str, Any], value: str):
        if value in input_data:
            return input_data[value]
        return self.flow_config[value]

    @staticmethod
    def _get_content(result):
        try:
            doc_file_name: str = result.download_pdf()
            with fitz.open(doc_file_name) as doc_file:
                text: str = "".join(page.get_text() for page in doc_file)
            return text
        except FileNotFoundError as f_ex:
            raise f_ex

    @flow_run_cache()
    def run(self, input_data: Dict[str, Any], expected_outputs: List[str]) -> Dict[str, Any]:
        query = input_data["query"]

        try:
            results = list(arxiv.Search(
                query=query,
                max_results=self._read_value(input_data, "max_results"),
                sort_by=self._read_value(input_data, "sort_by"),
                sort_order=self._read_value(input_data, "sort_order")
            ).results())
        except ArxivError as ex:
            raise ex

        if self._read_value(input_data, "get_basic_content"):
            return {expected_outputs[0]: [{
                "title": res.title,
                "summary": res.summary,
                "authors": [str(a) for a in res.authors],
                # "id": res.entry_id
            } for res in results]}

        if self._read_value(input_data, "get_content"):
            for res in tqdm.tqdm(results):
                res.text = self._get_content(res)

        return {expected_outputs[0]: results}

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
        expected_outputs=["arxiv_outputs"],
        get_content=False,
        get_basic_content=True
    )

    # ~~~ ArxivDocumentTransform ~~~
    arxiv_transform_flow = ArxivDocumentTransform(
        name="ArxivDocumentTransform",
        description="Takes the output of an ArxivAPIAtomicFlow and parses it into a string",
        expected_inputs=["arxiv_outputs"],
        expected_outputs=["paper_descriptions"]
    )

    # ~~~ SummarizerFlow ~~~
    sys_prompt = langchain.PromptTemplate(
        template="You are an expert in the field {{field}}, you are given the abstract of papers that appeared "
                 "yesterday in this field on arXiv. Provide a summary of what these works proposes for a researcher ("
                 "expert) in this field. In particular, focus on what is the novelty and place it the bigger context "
                 "of the work in this field. Your summary should be around 200 words.",
        input_variables=["field"],
        template_format="jinja2"
    )

    query_prompt = langchain.PromptTemplate(
        template="\nHere are the papers you should summarize:\n\n{{paper_descriptions}}",
        input_variables=["paper_descriptions"],
        template_format="jinja2"
    )
    hum_prompt = langchain.PromptTemplate(
        template="{{query}}",
        input_variables=["query"],
        template_format="jinja2"
    )

    summarizer_flow = OpenAIChatAtomicFlow(
        name="SummarizeArxiv",
        description="summarizes several arxiv paper",
        model_name="gpt-3.5-turbo",
        generation_parameters={},
        expected_inputs=["field", "paper_descriptions"],
        expected_outputs=["summary"],
        system_message_prompt_template=sys_prompt,
        human_message_prompt_template=hum_prompt,
        query_message_prompt_template=query_prompt
    )

    # ~~~ DailyArxivSummarizer ~~~
    daily_arxiv_summarizer = SequentialFlow(
        name="summarizer arxiv",
        description="summarizes arxiv",
        expected_inputs=["field", "max_results", "api_key"],
        expected_outputs=["summary"],
        flows={
            "arxiv_flow": arxiv_flow,
            "arxiv_transform_flow": arxiv_transform_flow,
            "summarizer_flow": summarizer_flow
        }
    )

    input_message = daily_arxiv_summarizer.package_task_message(
        recipient_flow=daily_arxiv_summarizer,
        task_name="summarize arxiv",
        task_data={
            "field": field,
            "query": query,
            "max_results": max_results,
            "api_key": os.getenv("OPENAI_API_KEY")},
        expected_outputs=["summary"]
    )

    answer = daily_arxiv_summarizer(input_message)
    print(answer.data)
