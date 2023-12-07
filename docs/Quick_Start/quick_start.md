# Quick Start

Welcome to the exciting world of aiFlows! 🚀

This quick start tutorial will guide you through your first inference runs, where we will address the task of question answering (QA) as a use case with  different Flows from the FlowVerse. In the process, you'll get familiar with the key aspects of the library and experience how, thanks to the modular abstraction and FlowVerse, we can trivially switch between very different pre-implemented question-answering Flows!

The guide is organized in three sections:
1. [Section 1:](#section-1-setting-up-aiflows) Setting up aiFlows
2. [Section 2:](#section-2-running-your-first-qa-flow-using-a-flow-from-the-flowverse) Running your first QA Flow using a Flow from the FlowVerse 🥳
3. [Section 3:](#section-3-flowverse-playground-notebook) FlowVerse Playground Notebook


## Section 1: Setting up aiFlows
Start off by installing the aiFlows with the [Setting Up aiFlows Tutorial](./setting_up_aiFlows.md)
#### By the Tutorial's End, I Will Have...
* Installed the aiFlows library successfully
* Established a file structure that allows me to effectively use all the features of the FlowVerse
* Set up a Hugging Face account allowing me to the FlowVerse (Optional)
* Configured and activated my API keys

## Section 2: Running your First QA Flow using a Flow from the FlowVerse

#### By the Tutorial's End, I Will Have...
* Learned how to pull Flows from the FlowVerse
* Run my first Flow
* Understood how to pass my API information to a Flow

While, we support many more API providers (including custom ones), for the sake of simplicity, in this tutorial, we'll assume you're using either using OpenAI or Azure.

### Step 1: Explore the FlowVerse
Discover a diverse range of Flows, including the [ChatFlowModule](https://huggingface.co/aiflows), by visiting our Flows on the FlowVerse[here](https://huggingface.co/aiflows). The `ChatAtomicFlow` within the `ChatFlowModule` is a versatile Flow that employs a language model (LLM) via an API to generate textual responses to textual inputs.

### Step 2: Pull From the FlowVerse 

To show you how to use a Flow from the FlowVerse, we will use the `ChatAtomicFlow`. The same process applies to any available Flow in the FlowVerse (implemented by any member of the community). Concretely, you would use the `sync_dependencies` function: 

```python
from flows import flow_verse
dependencies = [
{"url": "aiflows/ChatFlowModule", "revision": "main"}
]

flow_verse.sync_dependencies(dependencies)
```

Keep in mind that "aiflows" here refers to our organization on Hugging Face, and `ChatFlowModule` is the specific Flow module being pulled from the FlowVerse.

Each Flow on the FlowVerse should include a `pip_requirements.txt` file for external library dependencies (if it doesn't have any, the file should be empty). You can check its dependencies on the FlowVerse. As you can see [here](https://huggingface.co/aiflows/ChatFlowModule/blob/main/pip_requirements.txt), the `ChatFlowModule` doesn't have any external dependencies, so we're all set. In general, if there are any, you need to make sure to install them.

### Step 3: Run the Flow! 
Import the flow you've just pulled:
```python
from flow_modules.aiflows.ChatFlowModule import ChatAtomicFlow
```
Set your API information:
```python
api_information = [ApiInfo(backend_used="openai", api_key=os.getenv("OPENAI_API_KEY"))]
# Azure backend
# api_information = ApiInfo(backend_used = "azure",
#                           api_base = os.getenv("AZURE_API_BASE"),
#                           api_key = os.getenv("AZURE_OPENAI_KEY"),
#                           api_version =  os.getenv("AZURE_API_VERSION") )
```
Each flow from the FlowVerse should have a `demo.yaml` file, which is a demo configuration of how to instantiate the flow. Give it a quick look (`ChatFlowModule`'s configuration can be found [here](https://huggingface.co/aiflows/ChatFlowModule/blob/main/demo.yaml)) and then load it:

```python
from flows.utils.general_helpers import read_yaml_file
# get demo configuration
cfg = read_yaml_file("flow_modules/aiflows/ChatFlowModule/demo.yaml")
```
An attentive reader might have noticed that the field `flow.backend.api_infos` in `demo.yaml` is set to "???" (see a snippet of here below).
```yaml
flow:  # Overrides the ChatAtomicFlow config
  _target_: aiflows.ChatFlowModule.ChatAtomicFlow.instantiate_from_default_config

  name: "SimpleQA_Flow"
  description: "A flow that answers questions."

  # ~~~ Input interface specification ~~~
  input_interface_non_initialized:
    - "question"

  # ~~~ backend model parameters ~~
  backend:
    _target_: flows.backends.llm_lite.LiteLLMBackend
    api_infos: ???
```

The following overwrites the field with your respective API information:
```python
# put the API information in the config
cfg["flow"]["backend"]["api_infos"] = api_information
```

Instantiate your Flow:
```python
# ~~~ Instantiate the Flow ~~~
flow = ChatAtomicFlow.instantiate_from_default_config(**cfg["flow"])    
flow_with_interfaces = {
    "flow": flow,
    "input_interface": None,
    "output_interface": None,
}

```
Load some data and run your flow with the `FlowLauncher`:
```python
# ~~~ Get the data ~~~
data = {"id": 0, "question": "What is the capital of France?"} 

# ~~~ Run the Flow ~~~
_, outputs  = FlowLauncher.launch(
        flow_with_interfaces= flow_with_interfaces ,data=data
    )
    # ~~~ Print the output ~~~
flow_output_data = outputs[0]
print(flow_output_data)
```
Congratulations! You've successfully run your first question-answering Flow!

You can find this example in [runChatAtomicFlow.py](../../examples/quick_start/runChatAtomicFlow.py)

To run it, use the following commands in your terminal:
```bash
cd examples/quick_start/
python runChatAtomicFlow.py
```

Upon execution, the result should appear as follows:
```bash
[{'api_output': 'The capital of France is Paris.'}]
```

## Section 3: FlowVerse Playground Notebook

Want to quickly run some Flows from FlowVerse? Check out our jupyter notebook [flow_verse_playground.ipynb](../../examples/quick_start/flow_verse_playground.ipynb) where you can quicky switch between the following flows from the FlowVerse:

* [ChatFlowModule](https://huggingface.co/aiflows/ChatFlowModule)

* [ReAct](https://huggingface.co/aiflows/ControllerExecutorFlowModule)

* [ChatInteractiveFlowModule](https://huggingface.co/aiflows/ChatInteractiveFlowModule)

* [ChatWithDemonstrationsFlowModule](https://huggingface.co/aiflows/ChatWithDemonstrationsFlowModule)

* [AutoGPTFlowModule](https://huggingface.co/aiflows/AutoGPTFlowModule)

* [VisionFlowModule](https://huggingface.co/aiflows/VisionFlowModule)
