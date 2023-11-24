# AtomicFlow
The `AtomicFlow` class is a subclass of `Flow` and corresponds to an Input/Output interface around a tool (note that LMs are also tools in the Flows framework!). 

One notable example is the [ChatAtomicFlow](../flows/application_flows/OpenAIFlowModule/ChatAtomicFlow.py), which is a wrapper around the OpenAI chat API.

Another example is the [HumanInputFlow](../flows/application_flows/HumanInputFlowModule/HumanInputFlow.py), which takes a human input.

## Writing an Atomic Flow

Let's write an Atomic Flow that takes a number and returns the reverse of the number.

This is how the flow_config would look like as a YAML file:
```yaml
name: "ReverseNumber"
description: "A flow that takes in a number and reverses it."

input_data_transformations: []
input_keys:
  - "number"

output_data_transformations:
  - _target_: flows.data_transformations.KeyCopy
    old_key2new_key:
      raw_response.output_number: "reversed_number"
output_keys:
  - "reversed_number"
clear_flow_namespace_on_run_end: True
keep_raw_response: False  # Set to True to keep the raw flow response in the output data
```

Let's break it down:
- The `name` and `description` parameters are self-explanatory.
- The `verbose` parameter controls the verbosity of the logs for the Flow. 
- According to the default implementation, the `input_keys` and `output_keys` parameters specify the required items in the `input_data` and the `output_data`. They define the interface of the Flow.
- The `clear_flow_namespace_on_run_end` parameter controls whether the Flow namespace will be reset after the execution of the Flow. In our case, it doesn't matter because we don't have any stateful variables in the flow namespace. This parameter can be excluded and, by default, is set to true.
- Before any DataTranformations are applied, the Flow output is returned  `keep_raw_response` parameter 

The Flow class would be implemented as follows:
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
You can find this example [here](https://github.com/epfl-dlab/flows/tree/main/tutorials/minimal_reverse_number). Few other notable examples are the HumanInputFlow and the the FixedReply Flow.

Note that we can pass a Python dictionary as the `overrides` parameter and not rely on YAML files.