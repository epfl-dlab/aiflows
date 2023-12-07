# AutoGPT

## Definition

The `AutoGPT` flow is a circular flow that organizes the problem-solving process into four distinct subflows:

1. `ControllerFlow`: Given an a goal and observations (from past executions), it selects from a predefined set of actions, which are explicitly defined in the `ExecutorFlow`, the next action it should execute to get closer accomplishing its goal. In our configuration, we implement the `ControllerFlow` using the `ChatAtomicFlow`

2. `ExecutorFlow`:  Following the action selection by the `ControllerFlow`, the process moves to the `ExecutorFlow`. This is a branching flow that encompasses a set of subflows, with each subflow dedicated to a specific action. The `ExecutorFlow` executes the particular subflow associated with the action chosen by the `ControllerFlow`. In our setup, the `ExecutorFlow` includes the following individual flows:
    * `WikiSearchAtomicFlow`: This flow, given a "search term," executes a Wikipedia search and returns content related to the search term.
    * `LCToolFlow` using `DuckDuckGoSearchRun`: This flow, given a "query," queries the DuckDuckGo search API and retrieves content related to the query.

3. `HumanFeedbackFlow`: This flow prompts the user for feedback on the latest execution of the `ExecutorFlow`. The collected feedback is then conveyed back to the `ControllerFlow` to be considered in the subsequent execution step. Additionally, the flow is designed to have the capability to terminate the `ReActWithHumanFeedbackFlow` if the user expresses such a preference.

4. `MemoryFlow`: This flow is used to read and write and read memories stored of passed conversations in a database. These memories can be passed to the `ControllerFlow` enabling it to have a long term memory without having to transmit the entire message history to the language model (LLM). It's implemented with the `VectorStoreFlow`

## Topology

The sequence of execution for `AutoGPT`'s flows is circular and follows this specific order:

1. The `MemoryFlow` retrieves relevant information from memory
2. The `ControllerFlow` selects the next action to execute and prepares the input for the `ExecutorFlow`
3. The `ExecutorFlow` executes the action specified by the `ControllerFlow`
4. The `HumanFeedbackFlow` asks the user for feedback
5. The `MemoryFlow` writes relevant information to memory

Here's a broad overview of the  `AutoGPTFlow`:

```
| -------> Memory Flow -------> Controller Flow ------->|
^                                                       |      
|                                                       |
|                                                       v
| <----- HumanFeedback Flow <------- Executor Flow <----|
```



## Going Through

`VectorStoreFlow` acts as an encapsulation for LangChain's vector store-backend memory, which offers support for two types of operations:

- `read`: This operation involves retrieving the K most relevant documents from VectorDB based on the provided `content`.
- `write`: This operation is utilised to add the given `content` to VectorDB.

```python
def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
    response = {}

    operation = input_data["operation"]
    assert operation in ["write", "read"], f"Operation '{operation}' not supported"

    content = input_data["content"]
    if operation == "read":
        assert isinstance(content, str), f"Content must be a string, got {type(content)}"
        query = content
        retrieved_documents = self.vector_db.get_relevant_documents(query)
        response["retrieved"] = [doc.page_content for doc in retrieved_documents]
    elif operation == "write":
        if isinstance(content, str):
            content = [content]
        assert isinstance(content, list), f"Content must be a list of strings, got {type(content)}"
        documents = content
        documents = self.package_documents(documents)
        self.vector_db.add_documents(documents)
        response["retrieved"] = ""

    return response
```


It is essential to note that the VectorDB backend operates with instances of the `langchain.schema.Document` type. However, this class is not JSON-serializable, which makes it incompatible with our IO scheme. Therefore, when interacting with the VectorStoreFlow class, the input content should be of type `List[str]`, which will be converted to `List[Document]` using the `package_documents()` method. Furthermore, when retrieving documents, only the `content` field of the retrieved items is returned.

```python
@staticmethod
def package_documents(documents: List[str]) -> List[Document]:
    return [Document(page_content=doc, metadata={"": ""}) for doc in documents]
```

In the configuration, you have the flexibility to specify the `type` of VectorDB to be used. Currently, the options supported are [Chroma](https://python.langchain.com/docs/modules/data_connection/vectorstores/integrations/chroma) and [FAISS](https://python.langchain.com/docs/modules/data_connection/vectorstores/integrations/faiss), both of which work with OpenAI Embeddings. Hence, instantiation requires an OpenAI API key. Additionally, if needed, you can add other vector stores to the `_set_up_retriever()` method by consulting [LangChain's vector store documentation](https://python.langchain.com/docs/modules/data_connection/vectorstores/) for reference.

### LangChain Tool Flow

The `LCToolFlow` is an atomic flow functioning as an interface for LangChain tools. This flow operates by taking a `tool_input`, which corresponds to the tool's keyword arguments, as its input, and then provides the observation as its output.

```python
def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
    tool_input = {k: input_data[k] for k in self.get_mandatory_run_input_keys(input_data)}
    observation = self.backend.run(tool_input=tool_input)
    return {"observation": observation}
```

Using a tool with the `LCToolFlow` is a straightforward process. By setting the desired tool as the backend's `_target_`, you can seamlessly integrate it into your workflow. For a comprehensive list of compatible tools, please refer to the Integrations section in [LangChain's Tool documentation](https://python.langchain.com/docs/modules/agents/tools/).

```yaml
- _target_: flows.application_flows.LCToolFlowModule.LCToolFlow.instantiate_from_default_config
  overrides:
    name: "ddg_search"
    backend:
      _target_: langchain.tools.DuckDuckGoSearchRun
```

### Human Feedback Flow

The `HumanFeedbackFlow` is a specialised subclass of the `HumanInputFlow` that enables users to provide feedback at the conclusion of each iteration. This feedback is subsequently appended to the observation generated by the `ActionFlow`. By doing so, the feedback becomes part of the memory, thereby influencing the agent's decision-making process.

In the current context, if the user enters the command `q` or `stop`, the flow triggers an early exit by setting the early exit key to `True`, which leads to the termination
