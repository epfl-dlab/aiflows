# Quick Start

Welcome to the exciting world of aiFlows! 🚀

This quick start tutorial will guide you through running inference with your first question answering Flow using Flows from the FlowVerse. You'll see how you can run inference with your first question answering Flow, and you can trivially change between vastly different question answering Flows thanks to the modular abstraction and FlowVerse!

## 1. Setting up aiFlows
Start off by installing the aiFlows with the [Setting Up aiFlows Tutorial](./setting_up_aiFlows.md)
#### By the Tutorial's End, I Will Have...
* Installed the aiFlows library successfully
* Established an organized file structure for seamless collaboration within the FlowVerse
* Set up a Hugging Face account for contribution to the FlowVerse (Optional)
* Configured and activated my API keys

## 2. Running your First QA Flow using a Flow from the FlowVerse

### Step 1: Visit the FlowVerse
Visit our flows from the FlowVerse [here](https://huggingface.co/aiflows) to discover a variety of flows, including the [ChatFlowModule](https://huggingface.co/aiflows) which contains the `ChatAtomicFlow` a versatile flow that utilizes a language model (LLM) via an API to generate textual responses responses to textual inputs.

### Step 2: Pull From the FlowVerse 

To acquire a flow from the FlowVerse, we'll guide you through pulling the `ChatAtomicFlow`. The same process applies to any available flow in the FlowVerse. Pull the flow with aiFlows' `sync_dependencies` function: 

```python
from flows import flow_verse
dependencies = [
{"url": "aiflows/ChatFlowModule", "revision": "main"}
]

flow_verse.sync_dependencies(dependencies)
```

Keep in mind that "aiflows" signifies our organization on Hugging Face, and `ChatFlowModule` is the specific flow module being pulled from the FlowVerse

Each flow on the FlowVerse should include a `pip_requirements.txt` file for external library dependencies (even if it doesn't have any). You can check its dependencies on the FlowVerse. As seen [here](https://huggingface.co/aiflows/ChatFlowModule/blob/main/pip_requirements.txt), the `ChatFlowModule` doesn't have any external dependencies, so we're all set. However, if there are any, make sure to install them.

### Step 4: Run the Flow ! 

```python
# ~~~ Set the API information ~~~
api_information = [ApiInfo(backend_used="openai", api_key=os.getenv("OPENAI_API_KEY"))]

# get demo configuration
cfg = read_yaml_file("flow_modules/aiflows/ChatFlowModule/demo.yaml")

# put the API information in the config
cfg["flow"]["backend"]["api_infos"] = api_information

# ~~~ Instantiate the Flow ~~~
flow = ChatAtomicFlow.instantiate_from_default_config(**cfg["flow"])    
flow_with_interfaces = {
    "flow": flow,
    "input_interface": None,
    "output_interface": None,
}

# ~~~ Get the data ~~~
data = {"id": 0, "question": "What is the capital of France?"} 

# ~~~ Run the Flow ~~~
_, outputs  = FlowLauncher.launch(
        flow_with_interfaces= flow_with_interfaces ,data=data
    )
    # ~~~ Print the output ~~~
flow_output_data = outputs[0]
print(flow_output_data)
````

### Step 4: Run the flow !

Each Flow on the FlowVerse should include a `run.py` and a `demo.yaml` file which are sufficient for running the flow. Therefore you should already be able