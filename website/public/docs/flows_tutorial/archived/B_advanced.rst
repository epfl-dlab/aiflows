=================
Advanced tutorial
=================

In the previous tutorial we explained how to implement your first simple ``Flow``. You should be familiar with the following steps:
 * Derive from one of the abstract base classes
 * Implement a ``run`` method
 * be sure to store persistent state in ``flow_state``
 * If necessary, implement an ``initialize`` method, to reset ``flow_state`` to a valid initial state

You should also have seen how to use the messaging system:
 * you can create a ``TaskMessage`` with ``package_task_message``
 * Use ``__call__`` to consume a ``TaskMessage`` and return an ``OutputMessage``: ``output = flow(task_message)``
 * Use ``_update_state`` to modify the ``flow_state`` and log a ``StateUpdateMessage``

With this tutorial you're diving deeper: We create a ``Flow`` that downloads recent papers from arxiv.org and uses a ``ChatAtomicFlow`` to summarize them.
You'll also see our caching mechanism and how to interface with human input.

-----------------------------------------
Create a ``Flow`` to wrap a 3rd party API
-----------------------------------------

Let's create an ``ArxivAPIAtomicFlow`` that wraps the ``arxiv`` python package.
As your flows become more complex, it is important to verify that all required inputs are given. This is done by implementing ``expected_inputs_given_state``.::

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



Since a ``Flow`` is just a python class, you can add any helper methods you might need.
In this case we add a convenience method to read a value from the ``input_data`` or the ``flow_config``,
as well as a class method that can extract text from a pdf file.::

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


The ``run`` method is where the actual work is done.
As you've already seen, it takes the ``input_data`` and a list of ``expected_outputs``.
There is one important addition compared to the simple flows in our previous tutorial:
We use the ``@flow_run_cache`` decorator to cache the results of this flow.::

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


Now let's see this flow in action::

    field = "stat.ML"
    query = f"cat:{field}"
    max_results = 5

    arxiv_flow = ArxivAPIAtomicFlow(
        name="ArxivAPIAtomicFlow",
        description="Retrieves last n arxiv paper from a given field",
        sort_by=SortCriterion.SubmittedDate,
        expected_inputs=["field", "max_results"],
        expected_outputs=["arxiv_outputs"],
        get_content=False,
        get_basic_content=True
    )

    task = arxiv_flow.package_task_message(arxiv_flow, "download arxiv papers",
                                           {"field": field,
                                            "max_results": max_results,
                                            "query": query}, expected_outputs=["arxiv_outputs"])

    arxiv_outputs = arxiv_flow(task)
    print(arxiv_outputs.data["arxiv_outputs"])

If you run the code above repeatedly, you'll see that the results are cached.

------------------------------------------------------------------------------------------------------------------
Creating a postprocessing ``Flow`` and chaining it up with the ``ArxivAPIAtomicFlow``, using a ``SequentialFlow``
------------------------------------------------------------------------------------------------------------------

We now want to apply further post-processing to the documents we downloaded.
To keep the ``ArxivAPIAtomicFlow`` as modular and reusable as possible, we'll create a new ``Flow`` for this.
We call it the ``ArxivDocumentTransform``, you can take a look at the source code `here <https://github.com/epfl-dlab/flows/tree/main/tutorials/arxive_flows/b_document_transform.py/>`_.

The ``RockPaperScissorsJudge`` (from the previous tutorial), has shown how to create composite ``Flow``, i.e. a ``Flow`` that contains other ``Flow`` instances.
Here we want to chain up the ``ArxivAPIAtomicFlow`` and the ``ArxivDocumentTransform``.
For this scenario we offer a convenient ``SequentialFlow`` class which takes a list of ``Flow`` instances and executes them sequentially.
Plugging the two flows together becomes trivial::

    field = "stat.ML"
    query = f"cat:{field}"
    max_results = 5

    arxiv_flow = ArxivAPIAtomicFlow(
        name="ArxivAPIAtomicFlow",
        description="Retrieves last n arxiv paper from a given field",
        sort_by=SortCriterion.SubmittedDate,
        expected_inputs=["field", "max_results"],
        expected_outputs=["arxiv_outputs"],
        get_content=False,
        get_basic_content=True
    )

    arxiv_transform_flow = ArxivDocumentTransform(
        name="ArxivDocumentTransform",
        description="Takes the output of an ArxivAPIAtomicFlow and parses it into a string",
        expected_inputs=["arxiv_outputs"],
        expected_outputs=["paper_descriptions"]
    )

    arxiv_download_and_transform = SequentialFlow(
        name="summarizer arxiv",
        description="summarizes arxiv",
        expected_inputs=["field", "max_results"],
        expected_outputs=["paper_descriptions"],
        flows={
            "arxiv_flow": arxiv_flow,
            "arxiv_transform_flow": arxiv_transform_flow
        }
    )

    task = arxiv_download_and_transform.package_task_message(arxiv_download_and_transform, "download and process arxiv papers",
                                                        {"field": field, "max_results": max_results, "query": query},
                                                        ["paper_descriptions"])

    output = arxiv_download_and_transform(task)
    print(output.data["paper_descriptions"])


------------------------------------------------------------------------------------------------------------------
Introducing a LLM to summarize the papers
------------------------------------------------------------------------------------------------------------------

The ``SequentialFlow`` is a convenient way to chain up multiple ``Flow`` instances.
Another ready-to-use building block is the ``ChatAtomicFlow``.
It integrates the OpenAI API, as well as ``LangChain`` prompts, to interface with an LLM.
If your prompt templates take input variables, the ``ChatAtomicFlow`` will automatically populate them with values from its ``flow_state``.
The cooperation between ``LangChain``, ``OpenAI`` and our ``Flow`` instances is absolutely seamless. ::

    sys_prompt={
        "_target_": "langchain.PromptTemplate",
        "template": "You are an expert in the field {{field}}, you are given the abstract of papers that appeared "
                    "yesterday in this field on arXiv. Provide a summary of what these works proposes for a researcher ("
                    "expert) in this field. In particular, focus on what is the novelty and place it the bigger context "
                    "of the work in this field. Your summary should be around 200 words.",
        "input_variables": ["field"],
        "template_format": "jinja2"
    }
    query_prompt = {
        "_target_": "langchain.PromptTemplate",
        "template": "\nHere are the papers you should summarize:\n\n{{paper_descriptions}}",
        "input_variables": ["paper_descriptions"],
        "template_format": "jinja2",
    }
    hum_prompt = {
        "_target_": "langchain.PromptTemplate",
        "template":"{{query}}",
        "input_variables":["query"],
        "template_format":"jinja2"
    }

    summarizer_flow = ChatAtomicFlow(
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

Now we can use a ``SequentialFlow`` to run the three ``Flow`` instances in one chain::

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

    task = daily_arxiv_summarizer.package_task_message(
        recipient_flow=daily_arxiv_summarizer,
        task_name="summarize arxiv",
        task_data={
            "field": field,
            "query": query,
            "max_results": max_results,
            "api_key": os.getenv("OPENAI_API_KEY")},
        expected_outputs=["summary"]
    )

    answer = daily_arxiv_summarizer(task)
    print(answer.data)


The full source for this example is `here <https://github.com/epfl-dlab/flows/tree/main/tutorials/arxive_flows/c_paper_summary.py/>`_.
Thanks to the built-in caching mechanism, when you run the code twice, you'll see the following output:

 | Retrieved from cache: ArxivAPIAtomicFlow -- run(input_data.keys()=['query', 'max_results'], expected_outputs=['arxiv_outputs'])
 | Retrieved from cache: ArxivDocumentTransform -- run(input_data.keys()=['arxiv_outputs'], expected_outputs=['paper_descriptions'])
 | Retrieved from cache: ChatAtomicFlow -- run(input_data.keys()=['field', 'paper_descriptions'], expected_outputs=['summary'])

------------------------------------------------------------------------------------------------------------------
Adding a human in the loop
------------------------------------------------------------------------------------------------------------------

So far, the tutorial has only highlighted the expressiveness and convenience of the ``flows`` library.
But a ``Flow`` that can download and process recent arxiv papers could be quite useful in practice.
Let's implement a QA flow. It downloads the papers, summarizes them, and then allows a human to ask a free-form question about the papers.
The reply is given by a LLM, which is given the downloaded papers as context.
We can add human input by implementing a new ``HumanInputAtomicFlow`` ::

    class HumanInputAtomicFlow(AtomicFlow):

        # ...

        def run(self, input_data: Dict[str, Any], expected_outputs: List[str]) -> Dict[str, Any]:
            # sys_prompt = input_data["explanation_for_human_input"]
            user_input = input(self._get_input_message(input_data))
            return {expected_outputs[0]: user_input}

You can run the whole code (and maybe discover some useful recent publications) with this `code <https://github.com/epfl-dlab/flows/tree/main/tutorials/arxive_flows/d_qa_flow.py/>`_.
It takes some time to download the arxiv papers for the first time, but thanks to the caching, this is only done once.
