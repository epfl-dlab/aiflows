# AtomicFlow

This guide presents the concept of AtomicFlow and is organized into two sections:
1. [Section 1:](#section-1-defining-atomic-flows) Defining Atomic Flows
2. [Section 2:](##section-2-writing-your-first-atomic-flow) Writing Your First Atomic Flow

## Section 1: Defining Atomic Flows

The `AtomicFlow` class is a subclass of `Flow` and corresponds to an Input/Output interface around a tool (note that LMs are also tools in the Flows framework!).

In the paper it's defined as such:

> "
>
> An `Atomic Flow` is effectively a minimal wrapper around
> a tool and achieves two things:
> 1.  It fully specifies the tool (e.g., the most basic Atomic Flow around 
> GPT-4 would specify the prompts and the generation parameters)
> 2. It abstracts the complexity of the internal computation by exposing only a > standard message-based interface for exchanging information with other Flows.
>
> "

Examples of Atomic Flows include:
* A wrapper around an LLM ([ChatAtomicFlow](https://huggingface.co/aiflows/ChatFlowModule))
* A search engine API ([LCToolFlowModule](https://huggingface.co/aiflows/LCToolFlowModule))
* An interface with a human ([HumanStandardInputFlowModule](https://huggingface.co/aiflows/HumanStandardInputFlowModule)
)

## Section 2: Writing Your First Atomic Flow

As a starting example, let's create an Atomic Flow that takes a number and returns its reverse. (e.g., if the input is 1234, it should return 4321)

Here's how the `flow_config` looks as a YAML file (you can also check out [reverseNumberAtomic.yaml](../examples/minimal%20reverse%20number/reverseNumberAtomic.yaml)):

```yaml
name: "ReverseNumber"
description: "A flow that takes in a number and reverses it."

input_interface:
  _target_: flows.interfaces.KeyInterface
  keys_to_select: ["number"]

output_interface: # Connector between the Flow's output and the caller
  _target_: flows.interfaces.KeyInterface
  keys_to_rename:
    output_number: "reversed_number" # Rename the api_output to answer
```

Breaking it down:
- The `name` and `description` parameters are self-explanatory. When defining a Flow you must always define these parameters
- `input_interface` and `output_interface` define transformations to the input and output data before and after using the tool. In this case, the `input_interface` ensures the key `number` is in the input data dictionary and passes it to the flow. The `output_interface` renames the key `output_number` to `reversed_number` in the output data dictionary.

Now let's define the Flow. The class would be implemented as follows (you can also check out the py file [reverse_number_atomic.py](../examples/minimal%20reverse%20number/reverse_number_atomic.py)):
```python
class ReverseNumberAtomicFlow(AtomicFlow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def run(self,input_data: Dict[str, Any]) -> Dict[str, Any]:
        input_number = input_data["number"]
        output_number = int(str(input_number)[::-1])
        response = {"output_number": output_number}
        return response
```
and instantiate the Flow by executing:
```python
overrides_config = read_yaml_file("reverseNumberAtomic.yaml")

flow = ReverseNumberAtomicFlow.instantiate_from_default_config(overrides=overrides_config)
```
You can find this example [here](../examples/minimal%20reverse%20number/). Few other notable examples are [HumanStandardInputFlowModule](https://huggingface.co/aiflows/HumanStandardInputFlowModule) and the the [FixedReplyFlowModule](https://huggingface.co/aiflows/FixedReplyFlowModule) Flow.

Note that we can pass a Python dictionary as the `overrides` parameter and not rely on YAML files.

To run this Flow, execute the following commands in your terminal (make sure to clone the repository first):
```bash
cd examples/minimal\ reverse\ number/
python reverse_number_atomic.py
```