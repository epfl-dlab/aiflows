# Road to Implementing your first Flow
This file goes through some of the examples in this repository. The goal is to walk through the examples to better understand the Flows library to then implement our own Flow: Create a simple assistant Flow which, given a python file with a set of functions, is able to use them to accomplish a certain task while interacting with a user.

This tutorial is organized as such:
1. [Section 1](##-Getting-started-with-Flows-and-the-Flowverse) Getting started with Flows and the FlowVerse
2. [Section 2](##Exploring-and-understanding-the-Flows-examples): Exploring and understanding the Flows [examples](examples/) 

## Getting started with Flows and the Flowverse
First let's start creating setting up the Flow environment with cond:
```
conda create --name flows python=3.9
conda activate flows
pip install -e .
```

To be able to access the Flowvers we must do the following:
* Create a [huggingface](https://huggingface.co/join) account (don't forget to confirm your email address)
* Login to hugging face on the terminal:
    * Type the following in the token:
        ```
        huggingface-cli login
        ```
    * It will ask for a token. If you haven't [created one](https://huggingface.co/settings/tokens) (a read token should be sufficent), do it and copy paste it into the terminal

We're also going to be creating a repository where we'll be keeping our Flows and Flows from the FlowVerse:
```
mkdir FlowModule
```

Finally, let's set our API key as an environment variable for your conda environment:
* If you're using openAI:
    * write in your terminal:
        ```
        conda env config vars set OPENAI_API_KEY=<YOUR-OPEN-AI-API_KEY>
        ```
    * reactivate your conda environment:
        ```
        conda activate flows
        ```
    * To make sure that your key has been set as an environment variable (your environment variables should appear):
        ```
        conda env config vars list
        ```
* If you're using Azure:
    * write in your terminal:
        ```
        conda env config vars set AZURE_OPENAI_KEY=<YOUR-AZURE_OPENAI_KEY>
        conda env config vars set AZURE_API_BASE=<YOUR-AZURE_API_BASE>
        conda env config vars set AZURE_API_VERSION=<YOUR-AZURE_API_VERSION>
        ```
    * reactivate your conda environment:
        ```
        conda activate flows
        ```
    * To make sure that your key has been set as an environment variable (your environment variables should appear):
        ```
        conda env config vars list
        ```

Now that we're done with setting up everything, let's move to examples
## Exploring and understanding the Flows examples

### Understanding and running the Minimal QA example

#### Understanding the Minimal QA example

The first example we're going to be looking at is the [minimal QA](examples/minimal%20QA/) example. More specifically, the [run_qa_flow.py](examples/minimal%20QA/run_qa_flow.py) example. As this is the first flow we're looking at, we'll be extensively look at it's setup.

As we can see from the following lines in [run_qa_flow.py](examples/minimal%20QA/run_qa_flow.py):
```python
dependencies = [
    {"url": "aiflows/OpenAIChatFlowModule", "revision": "6a1e351a915f00193f18f3da3b61c497df1d31a3"},
]
```

This flow is built on the the `OpenAiChatFlowModule` flow hosted on the [FlowVerse](https://huggingface.co/aiflows). If you click [here](https://huggingface.co/aiflows/OpenAIChatFlowModule) you can see the `OpenAiChatFlowModule`. The `revision` key in the `dependencies` dictonary (from code here above) indicates the commit hash from which we will pulling from (to see the various commit hashes of  `OpenAiChatFlowModule` click [here](https://huggingface.co/aiflows/OpenAIChatFlowModule/commits/main)). 

The configuration of our flow is defined in [simpleQA.yaml](examples/minimal%20QA/run_qa_flow.py). The first line of the config file are the following:
```ruby
input_interface:  # Connector between the "input data" and the Flow
  _target_: flows.interfaces.KeyInterface
  additional_transformations:
    - _target_: flows.data_transformations.KeyMatchInput  # Pass the input parameters specified by the flow

output_interface:  # Connector between the Flow's output and the caller
  _target_: flows.interfaces.KeyInterface
  keys_to_rename:
    api_output: answer  # Rename the api_output to answer
```
As specified in the comments, the `input_interface` and `output_interface` contain the parameters necessary to configure the input and output interfaces of the flow (if you're unfamiliar with hydra and config files, make sure to go through the basic concepts by visiting the [hydra](https://hydra.cc/) homepage). The rest of the config configures the rest of the flow:
```ruby
flow:  # Overrides the OpenAIChatAtomicFlow config
  _target_: aiflows.OpenAIChatFlowModule.OpenAIChatAtomicFlow.instantiate_from_default_config

  name: "SimpleQA_Flow"
  description: "A flow that answers questions."

  # ~~~ Input interface specification ~~~
  input_interface_non_initialized:
    - "question"

  # ~~~ OpenAI model parameters ~~
  model: "gpt-3.5-turbo"
  generation_parameters:
    n: 1
    max_tokens: 3000
    temperature: 0.3

    model_kwargs:
      top_p: 0.2
      frequency_penalty: 0
      presence_penalty: 0

  n_api_retries: 6
  wait_time_between_retries: 20

  # ~~~ Prompt specification ~~~
  system_message_prompt_template:
    _target_: langchain.PromptTemplate
    template: |2-
      You are a helpful chatbot that truthfully answers questions.
    input_variables: []
    partial_variables: {}
    template_format: jinja2

  init_human_message_prompt_template:
    _target_: langchain.PromptTemplate
    template: |2-
      Answer the following question: {{question}}
    input_variables: ["question"]
    partial_variables: {}
    template_format: jinja2
```
Some interesting fields are:
* **`_target_: aiflows.OpenAIChatFlowModule.OpenAIChatAtomicFlow.instantiate_from_default_config`**: which specifies that we will be instantiatin the `OpenAIChatFlowModule` from a default configuration that we are specifying here
* **`input_interface_non_initialized:`**: Which indicates the various keys that will be included in our input
* **`model: "gpt-3.5-turbo"`**: Indicating we'll be using the "gpt-3.5-turbo" model from openAI as our LLM
* **`system_message_prompt_template:`**: Indicating the system prompt we will be feeding to the openAI model
* **`init_human_message_prompt_template`**: Indiciating the format of the user prompt we'll be feeding to the model.

Now going back to [run_qa_flow.py](examples/minimal%20QA/run_qa_flow.py), the next step is to setup our API keys (make sure you have set your API key as an environment variable as shown at end of [Section 1](##-Getting-started-with-Flows-and-the-Flowverse)):
```python
 # ~~~ Set the API information ~~~
    # OpenAI backend
    # api_information = ApiInfo("openai", os.getenv("OPENAI_API_KEY"))
    # Azure backend
    api_information = ApiInfo("azure", os.getenv("AZURE_OPENAI_KEY"), os.getenv("AZURE_OPENAI_ENDPOINT"))
```
IMPORTANT: if you're using an openAI key, you wil want to replace the lines above with:
```python
 # ~~~ Set the API information ~~~
    #OpenAI backend
    api_information = ApiInfo("openai", os.getenv("OPENAI_API_KEY"))
    #Azure backend
    #api_information = ApiInfo("azure", os.getenv("AZURE_OPENAI_KEY"), os.getenv("AZURE_OPENAI_ENDPOINT"))
```
The nex step is to instanstiate the flow and define the questions we would like to ask:
```python
# ~~~ Instantiate the Flow ~~~
    flow_with_interfaces = {
        "flow": hydra.utils.instantiate(cfg['flow'], _recursive_=False, _convert_="partial"),
        "input_interface": (
            None
            if getattr(cfg, "input_interface", None) is None
            else hydra.utils.instantiate(cfg['input_interface'], _recursive_=False)
        ),
        "output_interface": (
            None
            if getattr(cfg, "output_interface", None) is None
            else hydra.utils.instantiate(cfg['output_interface'], _recursive_=False)
        ),
    }

# ~~~ Get the data ~~~
    data = {"id": 0, "question": "What is the capital of France?"}  # This can be a list of samples
    # data = {"id": 0, "question": "Who was the NBA champion in 2023?"}  # This can be a list of samples

    # ~~~ Run inference ~~~
    path_to_output_file = None
    # path_to_output_file = "output.jsonl"  # Uncomment this line to save the output to disk

```
And finally we can lauche the flow with the `FlowLauncher`!
```python
 _, outputs = FlowLauncher.launch(
        flow_with_interfaces=flow_with_interfaces,
        data=data,
        path_to_output_file=path_to_output_file,
        api_information=api_information,
    )

    # ~~~ Print the output ~~~
    flow_output_data = outputs[0]
    print(flow_output_data)

```

Note that there's also an example of a multithreaded version of the minimalQA able to anser multiple questions with mulitple API_keys in [un_qa_flow_multithreaded.py](examples/minimasl%20QA/run_qa_flow_multithreaded.py).

#### Running the Minimal QA example
Now that we've understood how the flow works, let's run it!
```
cd examples/minimal\ QA
python run_qa_flow.py
```

### Atomic Flows
This section will present how to define an atomic Flow. To define an atomic flow, you need to files. A config file (in our case [reverseNumberAtomic.yaml](examples/minimal%20reverse%20number/reverseNumberAtomic.yaml)) and a python file where we'll be defining our flow (in our case [reverse_number_atomic.py](examples/minimal%20reverse%20number/reverse_number_atomic.py)). We will be defining a flow which is able to reverse a number.

Let's start by defining the `ReverseNumberAtomicFlow` class. To define a minimal atomic flow, you must at least redefine the `__init__` and the `run` function of the `AtomicFlow` class. In our case, we do not need to define any new class attributes so the `__init__` function is pretty straight forward. In the `run` function however, we will be defining the "algorithm" to reverse a number as such:
```python
class ReverseNumberAtomicFlow(AtomicFlow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def run(self,
            input_data: Dict[str, Any]) -> Dict[str, Any]:

        input_number = input_data["number"]
        output_number = int(str(input_number)[::-1])
        response = {"answer": output_number}
        return response

```

### AtomicFlow
The `AtomicFlow` class is a subclass of `Flow` and corresponds to an Input/Output interface around a tool (note that LMs are also tools in the Flows framework!). 

One notable example is the [OpenAIChatAtomicFlow](../flows/application_flows/OpenAIFlowModule/OpenAIChatAtomicFlow.py), which is a wrapper around the OpenAI chat API.

Another example is the [HumanInputFlow](../flows/application_flows/HumanInputFlowModule/HumanInputFlow.py), which takes a human input.

## Writing an Atomic Flow

Let's write an Atomic Flow that takes a number and returns the reverse of the number.

This is how the flow_config would look like as a YAML file:
```yaml
name: "ReverseNumber"
description: "A flow that takes in a number and reverses it."

output_interface:  # Connector between the Flow's output and the caller
  _target_: flows.interfaces.KeyInterface
  keys_to_rename:
    answer: "reversed_number" # Rename the api_output to answer

keep_raw_response: False  # Set to True to keep the raw flow response in the output data
```

Let's break it down:
- The `name` and `description` parameters are self-explanatory.
- The `output_interface` defines the interface at the output of our flow. For example, in our case, we are renaming in the output dictionary the "answer" (see output of `run` function in the ReverseNumberAtomicFlow class here below) key to "reversed number"

The Flow class would be implemented as follows:
```python
class ReverseNumberAtomicFlow(AtomicFlow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def run(self,
            input_data: Dict[str, Any]) -> Dict[str, Any]:

        input_number = input_data["number"]
        output_number = int(str(input_number)[::-1])
        response = {"answer": output_number}
        return response

```
 
and instantiate the Flow by executing:
```python
api_information = ApiInfo("noAPI","")

root_dir = "examples/minimal reverse number"
cfg_path = os.path.join(root_dir, "reverseNumberAtomic.yaml")
overrides_config = read_yaml_file(cfg_path)

# ~~~ Instantiate the flow ~~~
flow = ReverseNumberAtomicFlow.instantiate_from_default_config(overrides=overrides_config)

```
Note that we are not using an API here so we just provide a mock one. Finally, we can run inference with the flow laucher
```python
# ~~~ Get the data ~~~
data = {"id": 0, "number": 1234}  # This can be a list of samples
# ~~~ Run inference ~~~
_, outputs = FlowLauncher.launch(
    flow_with_interfaces={"flow": flow,
                            "output_interface": hydra.utils.instantiate(overrides_config['output_interface'], _recursive_=False)},
    data=data,
    path_to_output_file=path_to_output_file,
    api_information=api_information
)

# ~~~ Print the output ~~~
flow_output_data = outputs[0]
print(flow_output_data)
```
You can run this code with:
```
python examples/minimal\ reverse\ number/reverse_number_atomic.py 
```

You can find this example [here](https://github.com/epfl-dlab/flows/tree/main/tutorials/minimal_reverse_number). Few other notable examples are the HumanInputFlow and the the FixedReply Flow.

Note that we can pass a Python dictionary as the `overrides` parameter and not rely on YAML files.


# Notes/Questions
