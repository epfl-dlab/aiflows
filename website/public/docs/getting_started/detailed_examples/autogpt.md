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



## Subflows

### Memory Flow

We utilize the `ChromaDBFlow` from the [VectorStoreFlowModule](https://huggingface.co/aiflows/VectorStoreFlowModule) as the `MemoryFlow`. For a detailed understanding of its parameters, refer to its [`FlowCard`](https://huggingface.co/aiflows/VectorStoreFlowModule) for an extensive description of its parameters.

Like every flow, when `ChromaDBFlow`'s `run` is called  function is called:

```python
def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """ This method runs the flow. It runs the ChromaDBFlow. It either writes or reads memories from the database.
        
        :param input_data: The input data of the flow.
        :type input_data: Dict[str, Any]
        :return: The output data of the flow.
        :rtype: Dict[str, Any]
        """
        api_information = self.backend.get_key()

        if api_information.backend_used == "openai":
            embeddings = OpenAIEmbeddings(openai_api_key=api_information.api_key)
        else:
            # ToDo: Add support for Azure
            embeddings = OpenAIEmbeddings(openai_api_key=os.getenv("OPENAI_API_KEY"))
        response = {}

        operation = input_data["operation"]
        if operation not in ["write", "read"]:
            raise ValueError(f"Operation '{operation}' not supported")

        content = input_data["content"]
        if operation == "read":
            if not isinstance(content, str):
                raise ValueError(f"content(query) must be a string during read, got {type(content)}: {content}")
            if content == "":
                response["retrieved"] = [[""]]
                return response
            query = content
            query_result = self.collection.query(
                query_embeddings=embeddings.embed_query(query),
                n_results=self.flow_config["n_results"]
            )

            response["retrieved"] = [doc for doc in query_result["documents"]]

        elif operation == "write":
            if content != "":
                if not isinstance(content, list):
                    content = [content]
                documents = content
                self.collection.add(
                    ids=[str(uuid.uuid4()) for _ in range(len(documents))],
                    embeddings=embeddings.embed_documents(documents),
                    documents=documents
                )
            response["retrieved"] = ""

        return response
```
One can notice that `ChromaDBFlow` acts as an encapsulation for chromadb's vector store-backend memory, which offers support for two types of operations:

- `read`: This operation involves retrieving the `n_results` most relevant documents from ChromaDB based on the provided `content`.
- `write`: This operation is utilised to add the given `content` to VectorDB.

#### Additional Documentation:

* To delve into the extensive documentation for `ChromaDBFlow`, refer to its [FlowCard on the FlowVerse](https://huggingface.co/aiflows/VectorStoreFlowModule)
* Find `ChromaDBFlow`'s default [configuration here](https://huggingface.co/aiflows/VectorStoreFlowModule/blob/main/ChromaDBFlow.yaml)
* For more information on the `chromadb` library, explore its [documentation](https://docs.trychroma.com/)




### ControllerFlow

We utilize the `ControllerAtomicFlow` from the [ControllerExecutorFlowModule ](https://huggingface.co/aiflows/ControllerExecutorFlowModule) as the `ControllerFlow`. For a detailed understanding of its parameters, refer to its [`FlowCard`](https://huggingface.co/aiflows/ControllerExecutorFlowModule) for an extensive description of its parameters.

`ControllerAtomicFlow`'s `run` function looks like this:

```python
def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """ This method runs the flow. Note that the response of the LLM is in the JSON format, but it's not a hard constraint (it can hallucinate and return an invalid JSON)
        
        :param input_data: The input data of the flow.
        :type input_data: Dict[str, Any]
        :return: The output data of the flow (thought, reasoning, criticism, command, command_args)
        :rtype: Dict[str, Any]
        """
        api_output = super().run(input_data)["api_output"].strip()
        response = json.loads(api_output)
        return response
```

The `run` function is a straightforward wrapper around [ChatAtomicFlow](https://huggingface.co/aiflows/ChatFlowModule). The Language Model (LLM) responds in JSON format, but this isn't strictly enforced—it may occasionally return an invalid JSON. The soft constraint is set by the system prompt, detailed in [its default configuration](https://huggingface.co/aiflows/ControllerExecutorFlowModule/blob/main/ControllerAtomicFlow.yaml). This configuration specifies the expected output format and describes the available commands it has access to (these are the subflows of the `ExecutorFlow`). The system prompt template is as follows:

```yaml
system_message_prompt_template:
  _target_: aiflows.prompt_template.JinjaPrompt
  template: |2-
    You are a smart AI assistant. 
    
    Your decisions must always be made independently without seeking user assistance.
    Play to your strengths as an LLM and pursue simple strategies with no legal complications.
    If you have completed all your tasks, make sure to use the "finish" command.

    Constraints:
    1. No user assistance
    2. Exclusively use the commands listed in double quotes e.g. "command name"

    Available commands:
    {{commands}}

    Resources:
    1. Internet access for searches and information gathering.
    2. Long Term memory management.

    Performance Evaluation:
    1. Continuously review and analyze your actions to ensure you are performing to the best of your abilities.
    2. Constructively self-criticize your big-picture behavior constantly.
    3. Reflect on past decisions and strategies to refine your approach.
    4. Every command has a cost, so be smart and efficient. Aim to complete tasks in the least number of steps.
    You should only respond in JSON format as described below
    Response Format:
    {
    "thought": "thought",
    "reasoning": "reasoning",
    "plan": "- short bulleted\n- list that conveys\n- long-term plan",
    "criticism": "constructive self-criticism",
    "speak": "thoughts summary to say to user",
    "command": "command name",
    "command_args": {
        "arg name": "value"
        }
    }
    Ensure your responses can be parsed by Python json.loads
input_variables: ["commands"]
```
Where "{{commands}}" is the placeholder for the available commands which are added to the template when the `ControllerAtomicFlow` is being instantiated.

The goal and observations (from past executions) are passed via the `human_message_prompt` and the `init_human_message_prompt` who are the following:
```yaml
human_message_prompt_template:
    template: |2
    Potentially relevant information retrieved from your memory:
    {{memory}}
    =================
    Here is the response to your last action:
    {{observation}}
    Here is the feedback from the user:
    {{human_feedback}}
    input_variables:
    - "observation"
    - "human_feedback"
    - "memory"
input_interface_initialized:
    - "observation"
    - "human_feedback"
    - "memory"
```

#### Additional Documentation:

* To delve into the extensive documentation for `ControllerAtomicFlow`, refer to its [FlowCard on the FlowVerse](https://huggingface.co/aiflows/ControllerExecutorFlowModule)
* Find `ControllerAtomicFlow`'s default [configuration here](https://huggingface.co/aiflows/ControllerExecutorFlowModule/blob/main/ControllerAtomicFlow.yaml)


### ExecutorFlow

We utilize a [BranchingFlow](https://github.com/epfl-dlab/aiflows/blob/main/aiflows/base_flows/branching.py) from aiFlow's codebase  as the `ExecutorFlow`. The `ExecutorFlow` by default has two subflows which are the available commands the `ControllerFlow` can call:

#### 1. The LCToolFlow

The `LCToolFlow` is an atomic flow functioning as an interface for LangChain tools. This flow operates by taking a `tool_input`, which corresponds to the tool's keyword arguments, as its input, and then provides the observation as its output.

```python
 def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
    """ This method runs the flow. It runs the backend on the input data.
    
    :param input_data: The input data of the flow.
    :type input_data: Dict[str, Any]
    :return: The output data of the flow.
    :rtype: Dict[str, Any]
    """
    observation = self.backend.run(tool_input=input_data)

    return {"observation": observation}
```

Using a tool with the `LCToolFlow` is a straightforward process. By setting the desired tool as the backend's `_target_`, you can seamlessly integrate it into your workflow. For a comprehensive list of compatible tools, please refer to the Integrations section in [LangChain's Tool documentation](https://python.langchain.com/docs/modules/agents/tools/).

```yaml
- _target_: flow_modules.aiflows.LCToolFlowModule.LCToolFlow.instantiate_from_default_config
  overrides:
    name: "ddg_search"
    backend:
      _target_: langchain.tools.DuckDuckGoSearchRun
```

#### 2. The WikiSearchAtomicFlow

The `WikiSearchAtomicFlow` is also atomic flow and functions as an interface for Wikipedia's API. Given a `search_term`, it can execute a search on wikipedia and fetch page summaries to eventually pass it back to the `ControllerFlow` 
```python
def run(self,
            input_data: Dict[str, Any]) -> Dict[str, Any]:
        """ Runs the WikiSearch Atomic Flow. It's used to execute a Wikipedia search and get page summaries.
        
        :param input_data: The input data dictionary
        :type input_data: Dict[str, Any]
        :return: The output data dictionary
        :rtype: Dict[str, Any]
        """

        # ~~~ Process input ~~~
        term = input_data.get("search_term", None)
        api_wrapper = WikipediaAPIWrapper(
            lang=self.flow_config["lang"],
            top_k_results=self.flow_config["top_k_results"],
            doc_content_chars_max=self.flow_config["doc_content_chars_max"]
        )

        # ~~~ Call ~~~
        if page_content := api_wrapper._fetch_page(term):
            search_response = {"wiki_content": page_content, "relevant_pages": None}
        else:
            page_titles = api_wrapper.search_page_titles(term)
            search_response = {"wiki_content": None, "relevant_pages": f"Could not find [{term}]. similar: {page_titles}"}

        # Log the update to the flow messages list
        observation = search_response["wiki_content"] if search_response["wiki_content"] else search_response["relevant_pages"]
        return {"wiki_content": observation}
```

#### Additional Documentation:

*  Refer to [LCToolFlow's FlowCard](https://huggingface.co/aiflows/LCToolFlowModule) and [WikiSearchAtomicFlow's FlowCard](https://huggingface.co/aiflows/ControllerExecutorFlowModule) for further documentation


### Human Feedback Flow

We utilize the `HumanStandadInputFlow` from the [HumanStandardInputFlowModule ](https://huggingface.co/aiflows/HumanStandardInputFlowModule) as the `HumanFeedbackFlow`. For a detailed understanding of its parameters, refer to its [`FlowCard`](https://huggingface.co/aiflows/HumanStandardInputFlowModule) for an extensive description of its parameters.

Its `run` function enables users to provide feedback at the conclusion of each iteration. This feedback is subsequently appended to the observation generated by the `ExecutorFlow`. By doing so, the feedback becomes part of the memory, thereby influencing the agent's decision-making process.

```python
def run(self,
            input_data: Dict[str, Any]) -> Dict[str, Any]:
        """ Runs the HumanStandardInputFlow. It's used to read input from the user/human's standard input.
        
        :param input_data: The input data dictionary
        :type input_data: Dict[str, Any]
        :return: The output data dictionary
        :rtype: Dict[str, Any]
        """

        query_message = self._get_message(self.query_message_prompt_template, input_data)
        state_update_message = UpdateMessage_Generic(
            created_by=self.flow_config['name'],
            updated_flow=self.flow_config["name"],
            data={"query_message": query_message},
        )
        self._log_message(state_update_message)

        log.info(query_message)
        human_input = self._read_input()

        return {"human_input": human_input}
```

In the current context, if the user enters the command `q`, the flow triggers an early exit by setting the early exit key to `True`, which leads to the termination of the Flow.

#### Additional Documentation:

* To delve into the extensive documentation for `HumanStandardInputFlow`, refer to its [FlowCard on the FlowVerse](https://huggingface.co/aiflows/HumanStandardInputFlow)

