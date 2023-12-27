# Quick Start

Welcome to the exciting world of aiFlows! 🚀

This tutorial will guide you through your first inference runs with different Flows from the FlowVerse for the task of question answering (QA) as an example. In the process, you'll get familiar with the key aspects of the library and experience how, thanks to the modular abstraction and FlowVerse, we can trivially switch between very different pre-implemented question-answering Flows!

The guide is organized in two sections:
1. [Section 1:](#section-1-running-your-first-qa-flow-using-a-flow-from-the-flowverse) Running your first QA Flow using a Flow from the FlowVerse 🥳
2. [Section 2:](#section-2-flowverse-playground-notebook) FlowVerse Playground Notebook


## Section 1: Running your First QA Flow using a Flow from the FlowVerse

#### By the Tutorial's End, I Will Have...
* Learned how to pull Flows from the FlowVerse
* Run my first Flow
* Understood how to pass my API information to a Flow

While, we support many more API providers (including custom ones), for the sake of simplicity, in this tutorial, we will use OpenAI and Azure.

### Step 1: Pull a Flow From the FlowVerse

Explore a diverse array of Flows on the FlowVerse here. In this demonstration, we'll illustrate how to use a Flow from the FlowVerse, focusing on the `ChatAtomicFlow` within the `ChatFlowModule`. This versatile Flow utilizes a language model (LLM) via an API to generate textual responses for given textual inputs. It's worth noting the same process described here applies to any available Flow in the FlowVerse (implemented by any member of the community). 

Without further ado, let's dive in!



Concretely, you would use the `sync_dependencies` function to pull the flow definition and its code from the FlowVerse:

```python
from aiflows import flow_verse
dependencies = [
{"url": "aiflows/ChatFlowModule", "revision": "main"}
]

flow_verse.sync_dependencies(dependencies)
```

#### External Library Dependencies


Each Flow on the FlowVerse should include a `pip_requirements.txt` file for external library dependencies (if it doesn't have any, the file should be empty). You can check its dependencies on the FlowVerse. In general, if there are any, you need to make sure to install them.

As you can see [here](https://huggingface.co/aiflows/ChatFlowModule/blob/main/pip_requirements.txt), the `ChatFlowModule` doesn't have any external dependencies, so we're all set. 

### Step 3: Run the Flow!
After executing `sync_dependencies`, the code implementation of `ChatFlowModule` has been pulled into the local repository.
We can now just import it:
```python
from flow_modules.aiflows.ChatFlowModule import ChatAtomicFlow
```

Set your API information (copy-paste it):
```python

#OpenAI backend
api_key = "" # copy paste your api key here
api_information = [ApiInfo(backend_used="openai", api_key=api_key)]

# Azure backend
# api_key = "" # copy paste your api key here
# api_base = "" # copy paste your api base here
# api_version = "" #copypase your api base here
# api_information = ApiInfo(backend_used = "azure",
#                           api_base =api_base,
#                           api_key = api_version,
#                           api_version =  api_version )
```
Each flow from the FlowVerse should have a `demo.yaml` file, which is a demo configuration of how to instantiate the flow. 

Load the  `demo.yaml` configuration:
```python
from aiflows.utils.general_helpers import read_yaml_file
# get demo configuration
cfg = read_yaml_file("flow_modules/aiflows/ChatFlowModule/demo.yaml")
```

An attentive reader might have noticed that the field `flow.backend.api_infos` in `demo.yaml` is set to "???" (see a snippet here below).
```yaml
flow:  # Overrides the ChatAtomicFlow config
  _target_: flow_modules.aiflows.ChatFlowModule.ChatAtomicFlow.instantiate_from_default_config

  name: "SimpleQA_Flow"
  description: "A flow that answers questions."

  # ~~~ Input interface specification ~~~
  input_interface_non_initialized:
    - "question"

  # ~~~ backend model parameters ~~
  backend:
    _target_: aiflows.backends.llm_lite.LiteLLMBackend
    api_infos: ???
```

The following overwrites the field with your personal API information:
```python
# recursively find the 'api_infos' entry and put the API information in the config
quick_load(cfg, api_information, key="api_infos")
```
This is equivalent to the following:
```python
cfg["flow"]["backend"]["api_infos"] = api_information
```
However, with `quick_load`, we are able to quickly set all entries of api_infos, this is useful when we need to configure more than just one config entries.

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
Note that `input_interface` and `output_interface` are here to control the data that comes in and out of the flow. In this case, we don't need specific data manipulation, so we will leave to `None`.

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
___
You can find this example in [runChatAtomicFlow.py](https://github.com/epfl-dlab/aiflows/tree/main/examples/quick_start/runChatAtomicFlow.py)

To run it, use the following commands in your terminal (make sure to copy-paste your keys first):
```bash
cd examples/quick_start/
python runChatAtomicFlow.py
```

Upon execution, the result should appear as follows:
```bash
[{'api_output': 'The capital of France is Paris.'}]
```

## Section 2: FlowVerse Playground Notebook

Want to quickly run some Flows from FlowVerse? Check out our jupyter notebook [flow_verse_playground.ipynb](https://github.com/epfl-dlab/aiflows/tree/main/examples/quick_start/flow_verse_playground.ipynb) where you can quicky switch between the following flows from the FlowVerse:

* [ChatFlowModule](https://huggingface.co/aiflows/ChatFlowModule)

* [ReAct](https://huggingface.co/aiflows/ControllerExecutorFlowModule)

* [ChatInteractiveFlowModule](https://huggingface.co/aiflows/ChatInteractiveFlowModule)

* [ChatWithDemonstrationsFlowModule](https://huggingface.co/aiflows/ChatWithDemonstrationsFlowModule)

* [AutoGPTFlowModule](https://huggingface.co/aiflows/AutoGPTFlowModule)

* [VisionFlowModule](https://huggingface.co/aiflows/VisionFlowModule)
