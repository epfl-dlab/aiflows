# ReAct Tutorial
**Prequisites:** setting up your API keys (see [setting_up_aiFlows.md](./setting_up_aiFlows.md)), [Introducing the FlowVerse with a Simple Q&A Flow Tutorial](./intro_to_FlowVerse_minimalQA.md)

This guide introduces an implementation of the ReAct flow. The guide is organized in two sections:

1. [Section 1:](#section-1-whats-the-react-flow) What's The ReAct Flow ?
2. [Section 2:](#section-2-running-the-react-flow) Running the ReAct Flow

## Section 1:  What's The ReAct Flow ?

The ReAct flow,  as introduced in [ReAct: Synergizing Reasoning and Acting in Language Models](https://arxiv.org/pdf/2210.03629.pdf), represents a Circular flow that organizes the problem-solving process into two distinct flows:

1. `ControllerFlow`: Given an a goal and observations (from past executions), it selects from a predefined set of actions, which are explicitly defined in the `ExecutorFlow`, the next action it should execute to get closer accomplishing its goal. In our configuration, we implement the `ControllerFlow` using the `ChatAtomicFlow`

2. `ExecutorFlow`:  Following the action selection by the `ControllerFlow`, the process moves to the `ExecutorFlow`. This is a branching flow that encompasses a set of subflows, with each subflow dedicated to a specific action. The `ExecutorFlow` executes the particular subflow associated with the action chosen by the `ControllerFlow`. In our setup, the `ExecutorFlow` includes the following individual flows:
    * `WikiSearchAtomicFlow`: This flow, given a "search term," executes a Wikipedia search and returns content related to the search term.
    * `LCToolFlow` using `DuckDuckGoSearchRun`: This flow, given a "query," queries the DuckDuckGo search API and retrieves content related to the query.

These steps are repeated until an answer is obtained.

## Section 2: Running The ReAct Flow

In this section, we'll guide you through running the ReAct Flow.

For the code snippets referenced from this point onward, you can find them[here](../examples/ReAct/)

Now, let's delve into the details without further delay!

Similar to the [Introducing the FlowVerse with a Simple Q&A Flow](./intro_to_FlowVerse_minimalQA.md) tutorial (refer to that tutorial for more insights), we'll start by fetching some flows from the FlowVerse. Specifically, we'll fetch the `ControllerExecutorFlowModule`, which includes the `ControllerExecutorFlow` (the composite flow of `ControllerFlow` and `ExecutorFlow`) and the `WikiSearchAtomicFlow`. Additionally, we'll fetch the `LCToolFlow`, a flow capable of implementing the DuckDuckGo search flow.
```python
from flows import flow_verse

dependencies = [
    {"url": "aiflows/LCToolFlowModule", "revision": "f1020b23fe2a1ab6157c3faaf5b91b5cdaf02c1b"},
    {"url": "aiflows/ControllerExecutorFlowModule", "revision": "09cda9615e5c48ae18e2c1244519ed7321145187"},
]

flow_verse.sync_dependencies(dependencies)
```

Each flow on the FlowVerse includes a `pip_requirements.txt` file for external library dependencies. Check out the [pip_requirements.txt for the LCToolFlowModule](https://huggingface.co/aiflows/LCToolFlowModule/blob/main/pip_requirements.txt)) and [pip_requirements.txt for the ControllerExecutorFlowModule](https://huggingface.co/aiflows/ControllerExecutorFlowModule/blob/main/pip_requirements.txt). You'll notice the need to install the following external libraries:
```
pip install wikipedia==1.4.0
pip install langchain==0.0.336
pip install duckduckgo-search==3.9.6
```

Now that we've fetched the flows from the FlowVerse and installed their respective requirements, we can start creating our Flow.

The configuration for our flow can be found in [ReAct.yaml](../examples/ReAct/ReAct.yaml) and looks like this:
```yaml
flow:
  _target_: aiflows.ControllerExecutorFlowModule.ControllerExecutorFlow.instantiate_from_default_config
  max_rounds: 30

  ### Subflows specification
  subflows_config:
    Controller:
      _target_: aiflows.ControllerExecutorFlowModule.ControllerAtomicFlow.instantiate_from_default_config
      commands:
        wiki_search:
          description: "Performs a search on Wikipedia."
          input_args: ["search_term"]
        ddg_search:
          description: "Query the search engine DuckDuckGo."
          input_args: ["query"]
        finish:
          description: "Signal that the objective has been satisfied, and returns the answer to the user."
          input_args: ["answer"]
      backend:
        _target_: flows.backends.llm_lite.LiteLLMBackend
        api_infos: ???
        model_name:
          openai: "gpt-3.5-turbo"
          azure: "azure/gpt-4"

    Executor:
      _target_: flows.base_flows.BranchingFlow.instantiate_from_default_config
      subflows_config:
        wiki_search:
          _target_: aiflows.ControllerExecutorFlowModule.WikiSearchAtomicFlow.instantiate_from_default_config
        ddg_search:
          _target_: aiflows.LCToolFlowModule.LCToolFlow.instantiate_from_default_config
          backend:
            _target_: langchain.tools.DuckDuckGoSearchRun

```
Note that the Flow is instantiate from it's default config, so we are only defining the parameters we wish to override here. The `ControllerExecutorFlow`'s default config can be found [here](https://huggingface.co/aiflows/ControllerExecutorFlowModule/blob/main/ControllerExecutorFlow.yaml) and the `LCToolFlow` default config can be found [here](https://huggingface.co/aiflows/LCToolFlowModule/blob/main/LCToolFlow.yaml).

Here's a breakdown of this configuration:
* `flow` contains the parameters for our flow, including:
    * The `_target_` parameter specifies the instantiation method for our flow. In this instance, we're using it to instantiate the `ControllerExecutorFlow` from its default configuration file.
    * `max_rounds`: The maximum number of rounds the flow can run for. 
    * `subflows_config`: The configuration of the subflows (both the `ControllerFlow` and the `ExecutorFlow`):
        * `Controller`: The configuration of the controller flow:
            * `commands`: A dictionary containing the set of actions the ControllerExecutorFlow can call. Each key of the dictionary is the name of the action it can excute and it's items is a another dictionary containing the following parameters:
                * `description`: A description of what the action does (it's important to be clear since these description are passed to the system prompt to explain to the LLM what each action can do)
                *  `input_args`: The list of arguments required by a given action
            * `backend`: The backend used by the `ControllerFlow`(see the previous tutorial [Introducing the FlowVerse with a Simple Q&A Flow](./intro_to_FlowVerse_minimalQA.md) for a more detailed description of the backend)
        * `Executor`: The configuration of the `ExecutorFlow`:
            * `subflows_config`: The configuration of the subflows of the `ExecutorFlow`. Each subflow corresponds to an action defined in the `ControllerFlow` through the `commands` parameter. It is noteworthy  that the names of the `command` keys align with the names of the subflows in the Executor's `subflow_config`

Now that we've set up our configuration file, we can finally call our flow

Now that our configuration file is set up, we can proceed to call our flow. Begin by configuring your API information. Below is an example using an OpenAI key, along with examples for other API providers (in comment):

```python
 # ~~~ Set the API information ~~~
# OpenAI backend
api_information = [ApiInfo(backend_used="openai", api_key=os.getenv("OPENAI_API_KEY"))]
# Azure backend
# api_information = [ApiInfo(backend_used = "azure",
#                           api_base = os.getenv("AZURE_API_BASE"),
#                           api_key = os.getenv("AZURE_OPENAI_KEY"),
#                           api_version =  os.getenv("AZURE_API_VERSION") )]
```

Next, load the YAML configuration, insert your API information, 
and define the flow_with_interfaces dictionary:

```python
path_to_output_file = None
    # path_to_output_file = "output.jsonl"  # Uncomment this line to save the output to disk

    root_dir = "examples/ReAct"
    cfg_path = os.path.join(root_dir, "ReAct.yaml")
    cfg = read_yaml_file(cfg_path)
    # print(cfg["flow"].keys())
    cfg["flow"]["subflows_config"]["Controller"]["backend"]["api_infos"] = api_information

    # ~~~ Instantiate the Flow ~~~
    flow_with_interfaces = {
        "flow": hydra.utils.instantiate(cfg["flow"], _recursive_=False, _convert_="partial"),
        "input_interface": (
            None
            if cfg.get("input_interface", None) is None
            else hydra.utils.instantiate(cfg["input_interface"], _recursive_=False)
        ),
        "output_interface": (
            None
            if cfg.get("output_interface", None) is None
            else hydra.utils.instantiate(cfg["output_interface"], _recursive_=False)
        ),
    }
```
Finally, run the flow with FlowLauncher.
```python
 # ~~~ Get the data ~~~
# This can be a list of samples
# data = {"id": 0, "goal": "Answer the following question: What is the population of Canada?"}  # Uses wikipedia
data = {"id": 0, "goal": "Answer the following question: Who was the NBA champion in 2023?"}

# ~~~ Run inference ~~~
path_to_output_file = None
# path_to_output_file = "output.jsonl"  # Uncomment this line to save the output to disk

_, outputs = FlowLauncher.launch(
    flow_with_interfaces=flow_with_interfaces, data=data, path_to_output_file=path_to_output_file
)

# ~~~ Print the output ~~~
flow_output_data = outputs[0]
print(flow_output_data)
```

The full example is available [here](../examples/ReAct/) and can be executed as follows:

```bash
cd examples/ReAct
python run.py
```

Upon execution, the result appears as follows:
```bash
[{'answer': 'The NBA champion in 2023 was the Denver Nuggets.', 'status': 'finished'}]
```
Finally we have the correct answer!

However, let's consider a scenario where you want to instruct ReAct:

> **Answer the following question: What is the profession and date of birth of Michael Jordan?**

Where Michael Jordan is the Professor of Electrical Engineering and Computer Sciences and Professor of Statistics at Berkley. If you run this with ReAct, the obtained answer might look like this:

```bash
[{'answer': 'Michael Jordan is a former professional basketball player and an American businessman. He was born on February 17, 1963.', 'status': 'finished'}]
```
Which is not what we wanted ! This output does not align with our intended question.

To discover how to retrieve information on Michael Jordan, the Berkeley Professor, using aiFlows, refer to the next tutorial [ReActWithHumanFeedback](./reActwHumanFeedback.md), a flow that incorporates human feedback into the ReAct flow!





