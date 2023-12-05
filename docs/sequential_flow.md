# Sequential Flow
**Prerequisites:** [Atomic Flow Tutorial](./atomic_flow.md)


This guide presents the concept of a Sequential Flow and is organized into two sections:
1. [Section 1:](#section-1-defining-sequential-flows--composite-flows) Defining Sequential Flows
2. [Section 2:](#section-2-writing-your-first-sequential-flow) Writing Your First Atomic Flow

## Section 1: Defining Sequential Flows & Composite Flows

The SequentialFlow involves the execution of a series of Flows in sequence. It's a subclass of CompositeFlow.

In the associated paper, a Composite Flow is described as follows:

> "
>
> Composite Flows accomplish more challenging, higher-level goals by leveraging and coordinating
> other Flows. Crucially, thanks to their local state and standardized interface, Composite Flows
> can readily invoke Atomic Flows or other Composite Flows as part of compositional, structured
> interactions of arbitrary complexity. Enabling research on effective patterns of interaction is one of
> the main goals of our work.
>
> "

Therefore, a `SequentialFlow` is a specialized form of `CompositeFlow` that runs Flows sequentially.

Other types of Composit Flows inclue:
* `CircularFlow`: A series of flows excuted in a circular fashion (e.g [ReAct](../examples/ReAct/))
* `BranchingFlow`: A series of flows organized in a parallel fashion. The branch (Flow) executed depends on the input of the branching flow (e.g. [BranchingFlow](../flows/base_flows/branching.py))

## Section 2: Writing Your First Sequential Flow

As an introductory example, let's leverage the atomic flow created in the [previous tutorial](./atomic_flow.md) to construct a Sequential Flow. This Sequential Flow will take a number, reverse it, and then reverse it back again.

Given the input number 1234, the process should unfold as follows:

```rust
Input       |          Sequential Flow             |        Output          |
------------|--------------------------------------|------------------------|
            |                                      |                        |
1234 -------|---> Flow1 ---> 4321 ---> Flow2 ------|-----> 1234             |
            |                                      |                        |
            |                                      |                        |
```

Here's how the `flow_config` looks as a YAML file (you can alos check out [reverseNumberSequential.yaml](../examples/minimal%20reverse%20number/reverseNumberSequential.yaml)):
```yaml
name: "ReverseNumberTwice"
description: "A sequential flow that reverses a number twice."

input_interface:
  - "number"

output_interface:
  - "output_number"

subflows_config:
  first_reverse_flow:
    _target_: reverse_number_atomic.ReverseNumberAtomicFlow.instantiate_from_default_config
    name: "ReverseNumberFirst"
    description: "A flow that takes in a number and reverses it."
  second_reverse_flow:
    _target_: reverse_number_atomic.ReverseNumberAtomicFlow.instantiate_from_default_config
    name: "ReverseNumberSecond"
    description: "A flow that takes in a number and reverses it."

topology:
  - goal: reverse the input number
    # circular flow as the orchestrator, prepare the correct input for the agent
    input_interface:
      _target_: flows.interfaces.KeyInterface
      keys_to_select: ["number"]
    flow: first_reverse_flow
    output_interface:
      _target_: flows.interfaces.KeyInterface
      keys_to_rename:
        output_number: first_reverse_output
      keys_to_select: ["first_reverse_output"]
    reset: false

  - goal: reverse the output of the first reverse
    # circular flow as the orchestrator, prepare the correct input for the agent
    input_interface:
      _target_: flows.interfaces.KeyInterface
      keys_to_rename:
        first_reverse_output: number
      keys_to_select: ["number"]
    flow: second_reverse_flow
    output_interface:
      _target_: flows.interfaces.KeyInterface
      keys_to_select: ["output_number"]
    reset: false
```

Breaking it down:
* The `name` and `description` parameters are self-explanatory. When defining a Flow you must always define these parameters
* `input_interface` specifies the expected keys in the input data dictionary passed to the  `SequentialFlow`
* `output_interface`  outlines the expected keys in the output data dictionary produced by the `SequentialFlow`
* `subflows_config` s where we specify the flows that constitute our sequential flow. Each subflow is defined 
as a key-value pair in a dictionary, where the key is the name attributed to the subflow, and the value 
is a dictionary containing the configuration of the flow. In this case, flows are defined with their 
default configuration, with overrides for the `name` and `description` of the flow.
* `topology` defines the order in which flows are executed within our `SequentialFlow`. 
It also specifies the input and output interfaces for each flow. The fields in topology include:
    * `goal`: A description of the objective of the flow at the given execution step.
    * `flow`: The name of the flow to be invoked, matching the name defined in `subflows_config`.
    * `input_interface`: Specifies the series of transformations to the input data 
    dictionary before passing it to the tool.
    * `output_interface`:  Specifies the series of transformations to the output data dictionary 
    before passing it to the next flow.
    * `reset`: Determines whether to reset the state and history of the flow after calling it (i.e., deletes all message history and key-value pairs (cache) saved in the flow state). 


Note the importance of the transformations defined in the `input_interface` and `output_interface` 
within the `topology`. These transformations play a crucial role in establishing a connection 
between the two flows. Specifically, the `input_interface` of the second flow includes a transformation 
that renames the dictionary key `first_reverse_output`, which is passed by the first flow, to `number`. 
This ensures proper key naming and enables the seamless execution of the subsequent flow.

Now let's instantiate the `SequentialFlow` (you can alos check out the py file 
[reverse_number_sequential.py](../examples/minimal%20reverse%20number/reverse_number_sequential.py)):

```python
cfg_path = os.path.join(root_dir, "reverseNumberSequential.yaml")
cfg = read_yaml_file(cfg_path)

# ~~~ Instantiate the flow ~~~
flow = SequentialFlow.instantiate_from_default_config(**cfg)
```

There is no need to define any new class 
since the `SequentialFlow` is a [base_flow](../flows/base_flows/sequential.py) and we've already
defined the `ReverseNumberAtomicFlow` in the [previous tutorial](./atomic_flow.md) 
You can find this example [here](../examples/minimal%20reverse%20number/).

Note that we can pass a Python dictionary as the overrides parameter and not rely on YAML files.

To run this Flow, execute the following commands in your terminal (make sure to clone the repository first):
```bash
cd examples/minimal\ reverse\ number/
python reverse_number_sequential.py
```






.