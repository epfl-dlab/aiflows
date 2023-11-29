# Auto-GPT

As autonomous LLM-powered agents, autoGPT has the following components:

- An `AgentAtomicFlow`: This component evaluates the goal and execution history, determining the next course of action.
- An `ActionFlow`: Responsible for executing the action based on the newly generated command, and subsequently sending the observation back to the agent.

What sets Auto-GPT apart and makes it more powerful are the introduction of two new subflows:

- The `VectorStoreFlow`: This subflow retrieves pertinent history associated with the last action's observation. The retrieved information is then forwarded to the agent flow, where it is utilised to construct the prompt for the subsequent action.
- An optional `HumanFeedbackFlow`: This component allows for the incorporation of human feedback into the observation, further enhancing the agent's performance.

Furthermore, Auto-GPT is equipped with a highly versatile tool called the `LCToolFlow`, which provides a wide range of functionalities beyond the human-like Wikipedia search found in ReAct.

## Vector Store Flow

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
