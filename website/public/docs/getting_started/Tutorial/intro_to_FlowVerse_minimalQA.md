
# Introducing the FlowVerse with a Simple Q&A Flow
**Prerequisites:** setting up your API keys (see [setting_up_aiFlows.md](./setting_up_aiFlows.md)), [Atomic Flow Tutorial](./atomic_flow.md)

This guide introduces the FlowVerse via an example: [minimalQA](https://github.com/epfl-dlab/aiflows/tree/main/examples/minimal%20QA/). The guide is organized in two sections:
1. [Section 1:](#section-1-whats-the-flowverse) What's the FlowVerse?
2. [Section 2:](#section-2-crafting-a-simple-qa-flow-with-the-chatflowmodule) Crafting a Simple Q&A Flow with the ChatFlowModule

### By the Tutorial's End, I Will Have...

* Gained an understanding of the FlowVerse and its significance
* Acquired the skills to retrieve flows from the FlowVerse
* Successfully developed my initial flow by incorporating a FlowVerse flow
* Created a Simple Q&A flow capable of managing user-assistant interactions with a Language Model (LLM) through an API
* Familiarized myself with the fundamental parameters of the `ChatAtomicFlow`

## Section 1: What's the FlowVerse ? 
The FlowVerse is the hub of flows created and shared by our amazing community for everyone to use! These flows are usually shared on Hugging Face with the intention of being reused by others. Explore our Flows on the FlowVerse [here](https://huggingface.co/aiflows)!

## Section 2: Crafting a Simple Q&A Flow with the ChatFlowModule

In this section, we'll guide you through the creation of a simple Q&A flow — a single user-assitant interaction with a LLM. We'll achieve this by leveraging the `ChatAtomicFlow` from the [ChatFlowModule](https://huggingface.co/aiflows/ChatFlowModule) in the FlowVerse. The `ChatAtomicFlow` seamlessly interfaces with an LLM through an API, generating textual responses for textual input. Powered by the LiteLLM library in the backend, `ChatAtomicFlow` supports various API providers; explore the full list [here](https://docs.litellm.ai/docs/providers).

For an in-depth understanding of `ChatAtomicFlow`, refer to its [FlowCard (README)](https://huggingface.co/aiflows/ChatFlowModule/blob/main/README.md).
Note that all the code referenced from this point onwards can be found [here](https://github.com/epfl-dlab/aiflows/tree/main/examples/minimal%20QA/)

Let's dive in without further delay!

First thing to do is to fetch the `ChatFlowModule` from the FlowVerse (see [run_qa_flow.py](https://github.com/epfl-dlab/aiflows/tree/main/examples/minimal%20QA/run_qa_flow.py) to see all the code):
```python
from aiflows import flow_verse
# ~~~ Load Flow dependecies from FlowVerse ~~~
dependencies = [
    {"url": "aiflows/ChatFlowModule", "revision": "297c90d08087d9ff3139521f11d1a48d7dc63ed4"},
]
flow_verse.sync_dependencies(dependencies)
```
Let's break this down:
* `dependencies` is a list of dictionaries (in this case, there's only one) indicating which FlowModules we want to pull from the FlowVerse. The dictionary contains two key-value pairs:
  * `url`: Specifies the URL where the flow can be found on Hugging Face. Here, the URL is `aiflows/ChatFlowModule`, where `aiflows` is the name of our organization on Hugging Face (or the username of a user hosting their flow on Hugging Face), and `ChatFlowModule` is the name of the FlowModule containing the `ChatAtomicFlow` on the FlowVerse. Note that the `url` is literally the address of the `ChatFlowModule` on Hugging Face (excluding the https://huggingface.co/). So if you type https://huggingface.co/aiflows/ChatFlowModule in your browser, you will find the Flow.
  * `revision`: Represents the revision id (i.e., the full commit hash) of the commit we want to fetch. Note that if you set `revision` to `main`, it will fetch the latest commit on the main branch.

Now that we've fetched the `ChatAtomicFlowModule` from the FlowVerse, we can start creating our Flow.

The configuration for our flow is available in [simpleQA.yaml](https://github.com/epfl-dlab/aiflows/tree/main/examples/minimal%20QA/simpleQA.yaml). We will now break it down into chunks and explain its various parameters. Note that the flow is instantiated from its default configuration, so we are only defining the parameters we wish to override here. The default configuration can be found [here](https://huggingface.co/aiflows/ChatFlowModule/blob/main/ChatAtomicFlow.yaml)

Let's start with the input and output interface:
```yaml
input_interface: # Connector between the "input data" and the Flow
  _target_: aiflows.interfaces.KeyInterface
  additional_transformations:
    - _target_: aiflows.data_transformations.KeyMatchInput # Pass the input parameters specified by the flow

output_interface: # Connector between the Flow's output and the caller
  _target_: aiflows.interfaces.KeyInterface
  keys_to_rename:
    api_output: answer # Rename the api_output to answer
```
* `input_interface` specifies the expected keys in the input data dictionary passed to our flow.
* `output_interface`  outlines the expected keys in the output data dictionary produced by our flow.

Now let's look at the flow's configuration:
```yaml
flow: # Overrides the ChatAtomicFlow config
  _target_: flow_modules.aiflows.ChatFlowModule.ChatAtomicFlow.instantiate_from_default_config

  name: "SimpleQA_Flow"
  description: "A flow that answers questions."
```

* The `_target_` parameter specifies the instantiation method for our flow. In this instance, we're using it to instantiate the `ChatAtomicFlow` from [its default configuration file](https://huggingface.co/aiflows/ChatFlowModule/blob/main/ChatAtomicFlow.yaml)
* `name` and `description`: self-explanatory parameters 
  

```yaml
  # ~~~ Input interface specification ~~~
  input_interface_non_initialized:
    - "question"
```
*  The `input_interface_non_initialized` parameter in our configuration specifies the keys expected in the input data dictionary when the `ChatAtomicFlow` is called for the first time (i.e., when the system prompt is constructed). Essentially, it serves a role similar to the regular `input_interface`. The distinction becomes apparent when you require different inputs for the initial query compared to subsequent queries. For instance, in ReAct, the first time you query the LLM, the input is provided by a human, such as a question. In subsequent queries, the input comes from the execution of a tool (e.g. a query to wikipedia). In ReAct's case, these two scenarios are distinguished by `ChatAtomicFlow`'s `input_interface_non_initialized` and `input_interface_initialized` parameters. For this tutorial, as we're creating a simple Q&A flow performing a single user-assistant interaction with an LLM, we never use `input_interface_initialized` (which is why it's not defined in the configuration).
  
```yaml
  # ~~~ backend model parameters ~~
  backend:
    _target_: aiflows.backends.llm_lite.LiteLLMBackend
    api_infos: ???
    model_name:
      openai: "gpt-3.5-turbo"
      azure: "azure/gpt-4"

    # ~~~ generation_parameters ~~
    n: 1
    max_tokens: 3000
    temperature: 0.3

    top_p: 0.2
    frequency_penalty: 0
    presence_penalty: 0
```
*  `backend` is a dictionary containing parameters specific to the LLM. These parameters include:
    * `api_infos` Your API information (which will be passed later for privacy reasons).
    * `model_name` A dictionary with key-item pairs, where keys correspond to the `backend_used` attribute of the `ApiInfo` class for the chosen backend, and values represent the desired model for that backend. Model selection depends on the provided `api_infos`. Additional models can be added for different backends, following LiteLLM's naming conventions (refer to LiteLLM's supported providers and model names [here](https://docs.litellm.ai/docs/providers)). For instance, with an Anthropic API key and a desire to use "claude-2," one would check Anthropic's model details [here](https://docs.litellm.ai/docs/providers/anthropic#model-details). As "claude-2" is named the same in LiteLLM, the `model_name` dictionary would be updated as follows:
      ```yaml
      backend:
      _target_: aiflows.backends.llm_lite.LiteLLMBackend
      api_infos: ???
      model_name:
        openai: "gpt-3.5-turbo"
        azure: "azure/gpt-4"
        anthropic: "claude-2"
      ```
    * `n`,`max_tokens`,`top_p`, `frequency_penalty`, `presence_penalty` are generation parameters for LiteLLM's completion function (refer to all possible generation parameters [here](https://docs.litellm.ai/docs/completion/input#input-params-1)).


```yaml
  # ~~~ Prompt specification ~~~
  system_message_prompt_template:
    _target_: aiflows.prompt_template.JinjaPrompt
    template: |2-
      You are a helpful chatbot that truthfully answers questions.
    input_variables: []
    partial_variables: {}

  init_human_message_prompt_template:
    _target_: aiflows.prompt_template.JinjaPrompt
    template: |2-
      Answer the following question: {{question}}
    input_variables: ["question"]
    partial_variables: {}

```
* `system_message_prompt_template`: This is the system prompt template passed to the LLM.
* `init_human_message_prompt_template`: This is the user prompt template passed to the LLM the first time the flow is called. It includes the following parameters:
  * `template` The prompt template in Jinja format.
  * `input_variables` The input variables of the prompt. For instance, in our case, the prompt `template` 
    is "Answer the following question: {{question}}," and our `input_variables`  is "question." Before querying the LLM, the prompt `template` is rendered by placing the input variable "question" in the placeholder "{{question}}" of the prompt `template`.  It's worth noting that  `input_interface_non_initialized == input_variables`. This alignment is intentional, as they are passed as input_variables to the `init_human_message_prompt_template` to render the `template`


Now that our configuration file is set up, we can proceed to call our flow. Begin by configuring your API information. Below is an example using an OpenAI key, along with examples for other API providers (in comment):
```python
 # ~~~ Set the API information ~~~
# OpenAI backend

api_information = [ApiInfo(backend_used="openai", api_key=os.getenv("OPENAI_API_KEY"))]

# # Azure backend
# api_information = [ApiInfo(backend_used = "azure",
#                           api_base = os.getenv("AZURE_API_BASE"),
#                           api_key = os.getenv("AZURE_OPENAI_KEY"),
#                           api_version =  os.getenv("AZURE_API_VERSION") )]

# # Anthropic backend
#api_information = [ApiInfo(backend_used= "anthropic",api_key = os.getenv("ANTHROPIC_API_KEY"))]

```
Next, load the YAML configuration, insert your API information, and define the `flow_with_interfaces` dictionary:
```python

cfg_path = os.path.join(root_dir, "simpleQA.yaml")
cfg = read_yaml_file(cfg_path)
# put api information in config (done like this for privacy reasons)
cfg["flow"]["backend"]["api_infos"] = api_information

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
Finally, run the flow with `FlowLauncher`.
```python
# ~~~ Get the data ~~~
data = {"id": 0, "question": "Who was the NBA champion in 2023?"}  # This can be a list of samples

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

The full example is available [here](https://github.com/epfl-dlab/aiflows/tree/main/examples/minimal%20QA/) and can be executed as follows:

```bash
cd examples/minimal\ QA/
python run_qa_flow.py 
```

Upon running, the answer is similar to the following:
```bash
[{'answer': "I'm sorry, but as an AI language model, I don't have access to real-time information or the ability to predict future events. As of now, I cannot provide you with the answer to who the NBA champion was in 2023. I recommend checking reliable sports news sources or conducting an internet search for the most up-to-date information."}]
```
To learn how to obtain information on the 2023 NBA Champion using Flows, refer to the next tutorial [ReAct](./reAct.md), a Flow that provides `ChatAtomicFlow` to tools like search engines!

Additionally, the [minimal QA](https://github.com/epfl-dlab/aiflows/tree/main/examples/minimal%20QA/) folder contains other examples using `ChatAtomicFlow` such as:
* Running a [Flow with Demonstrations](https://github.com/epfl-dlab/aiflows/tree/main/examples/minimal%20QA/run_qa_flow_w_demonstrations.py) (encouraging the LLM to finshis answers with "my sire"). To run:
  ```bash
  cd examples/minimal\ QA/
  python run_qa_flow_w_demonstrations.py
  ```
* Running the [Simple Q&A flow in a multithreaded fashion](https://github.com/epfl-dlab/aiflows/tree/main/examples/minimal%20QA/run_qa_flow_multithreaded.py) in order answer multiple questions with mulitple API_keys or providers. To run:
  ```bash
  cd examples/minimal\ QA/
  python run_qa_flow_multithreaded.py
  ```
___


**Next Tutorial:** [ReAct Tutorial](./reAct.md)





