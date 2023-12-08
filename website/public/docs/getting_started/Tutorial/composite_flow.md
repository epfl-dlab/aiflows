# Composite Flow Tutorial
**Prerequisites:** [Atomic Flow Tutorial](./atomic_flow.md)


This guide introduces the concept of a composite flow by illustrating the creation of a sequential flow, a specific type of composite flow. The content is structured into two main sections:
1. [Section 1:](#section-1-defining-composite-flows-and-sequential-flows) Defining Composite Flows and Sequential Flows
2. [Section 2:](#section-2-writing-your-first-sequential-flow) Writing Your First Sequential Flow

### By the Tutorial's End, I Will Have...

* Gained insights into the concept of a Composite Flow
* Acquired the skills to create a `SequentialFlow` through a toy example
* Developed an understanding of the utility of input and output interfaces in connecting subflows within the flow structure


## Section 1: Defining Composite Flows and Sequential Flows

A `SequentialFlow` entails the sequential execution of a series of flows. It's a subclass of `CompositeFlow`.

In the paper, a Composite Flow is described as follows:

> 
>
> Composite Flows accomplish more challenging, higher-level goals by leveraging and coordinating
> other Flows. Crucially, thanks to their local state and standardized interface, Composite Flows
> can readily invoke Atomic Flows or other Composite Flows as part of compositional, structured
> interactions of arbitrary complexity. Enabling research on effective patterns of interaction is one of
> the main goals of our work.
>
> 

Therefore, a `SequentialFlow` is a specialized form of `CompositeFlow` that runs Flows sequentially.

Other types of Composite Flows include:
* `CircularFlow`: A series of flows excuted in a circular fashion (e.g [ReAct](https://github.com/epfl-dlab/aiflows/tree/main/examples/ReAct/))
* `BranchingFlow`: A series of flows organized in a parallel fashion. The branch (Flow) executed depends on the input of the branching flow (e.g. [BranchingFlow](https://github.com/epfl-dlab/aiflows/tree/main/aiflows/base_flows/branching.py))

## Section 2: Writing Your First Sequential Flow

As an introductory example, let's leverage the atomic flow created in the previous tutorial ([Atomic Flow Tutorial](./atomic_flow.md)) to construct a `SequentialFlow`. This `SequentialFlow` will take a number, reverse it, and then reverse it back again.

Given the input number 1234, the process should unfold as follows:

```rust
Input       |          Sequential Flow             |        Output          
------------|--------------------------------------|--------------
            |                                      |                        
1234 -------|---> Flow1 ---> 4321 ---> Flow2 ------|-----> 1234             
            |                                      |                        
            |                                      |                        
```

The flow configuration, presented as a YAML file, is outlined below (you can also review the configuration in [reverseNumberSequential.yaml](https://github.com/epfl-dlab/aiflows/tree/main/examples/minimal%20reverse%20number/reverseNumberSequential.yaml)):
```yaml
name: "ReverseNumberTwice"
description: "A sequential flow that reverses a number twice."

# input and output interfaces of SequentialFlow
input_interface:
  - "number"

output_interface:
  - "output_number"

#configuration of subflows
subflows_config:
  first_reverse_flow:
    _target_: reverse_number_atomic.ReverseNumberAtomicFlow.instantiate_from_default_config
    name: "ReverseNumberFirst"
    description: "A flow that takes in a number and reverses it."
  second_reverse_flow:
    _target_: reverse_number_atomic.ReverseNumberAtomicFlow.instantiate_from_default_config
    name: "ReverseNumberSecond"
    description: "A flow that takes in a number and reverses it."

# Define order of execution of subflows and input & output interfaces for proper execution
topology:
  #fist flow to execute
  - goal: reverse the input number
    input_interface:
      _target_: aiflows.interfaces.KeyInterface
      keys_to_select: ["number"]
    flow: first_reverse_flow
    output_interface:
      _target_: aiflows.interfaces.KeyInterface
      keys_to_rename:
        output_number: first_reverse_output
      keys_to_select: ["first_reverse_output"]
    reset: false
  #second flow to execute
  - goal: reverse the output of the first reverse
    input_interface:
      _target_: aiflows.interfaces.KeyInterface
      keys_to_rename:
        first_reverse_output: number
      keys_to_select: ["number"]
    flow: second_reverse_flow
    output_interface:
      _target_: aiflows.interfaces.KeyInterface
      keys_to_select: ["output_number"]
    reset: false

```

Breaking it down:
* The `name` and `description` parameters are self-explanatory. When defining a Flow you must always define these parameters

* `input_interface` specifies the expected keys in the input data dictionary passed to the  `SequentialFlow`

* `output_interface`  outlines the expected keys in the output data dictionary produced by the `SequentialFlow`

* In the `subflows_config`, the specification of flows constituating the `SequentialFlow` are detailed. Each subflow is articulated as a key-item pair within a dictionary. The key denotes the name assigned to the subflow, while the corresponding item is a dictionary encapsulating the configuration of the subflow. In this instance, subflows are outlined with their default configuration, incorporating overrides for the `name` and `description` of each flow.

* `topology` defines the order in which flows are executed within our `SequentialFlow`. 
It also specifies the input and output interfaces for each flow. The fields in topology include:
    * `goal`: A description of the objective of the flow at the given execution step.
    * `flow`: The name of the flow to be invoked, matching the name defined in `subflows_config`.
    * `input_interface`: Specifies the transformation to the input data 
    dictionary before passing it to the current subflow.
    * `output_interface`:  Specifies the transformation to the output data dictionary 
    before passing it to the next subflow.
    * `reset`: Determines whether to reset the state and history of the flow after calling it (i.e., deletes all message history and key-value pairs (cache) saved in the flow state). 


Note the importance of the transformations defined in the `input_interface` and `output_interface` 
within the `topology`. These transformations play a crucial role in establishing a connection 
between the two flows. Specifically, the `input_interface` of the `second_reverse_flow` includes a transformation 
that renames the dictionary key `first_reverse_output`, which is passed by the `first_reverse_flow`, to `number`. 
This ensures proper key naming and enables the seamless execution of the subsequent flow.

Now let's instantiate the `SequentialFlow` (you can also check out the py file 
[reverse_number_sequential.py](https://github.com/epfl-dlab/aiflows/tree/main/examples/minimal%20reverse%20number/reverse_number_sequential.py)):

```python
cfg_path = os.path.join(root_dir, "reverseNumberSequential.yaml")
cfg = read_yaml_file(cfg_path)

# ~~~ Instantiate the flow ~~~
flow = SequentialFlow.instantiate_from_default_config(**cfg)
```

There is no need to define any new class 
since the `SequentialFlow` is a [base_flow](https://github.com/epfl-dlab/aiflows/tree/main/aiflows/base_flows/sequential.py) (meaning it's already defined in the aiFlows library) and we've already
defined the `ReverseNumberAtomicFlow` in the previous tutorial ([Atomic Flow Tutorial](./atomic_flow.md)) 

With all the preparations in place, we can now proceed to invoke our flow and execute it using the `FlowLauncher`.

```python
# ~~~ Get the data ~~~
data = {"id": 0, "number": 1234}  # This can be a list of samples

# ~~~ Run inference ~~~
path_to_output_file = None
# path_to_output_file = "output.jsonl"
_, outputs = FlowLauncher.launch(
    flow_with_interfaces={"flow": flow}, data=data, path_to_output_file=path_to_output_file
)

# ~~~ Print the output ~~~
flow_output_data = outputs[0]
print(flow_output_data)
```

The complete example is accessible [here](https://github.com/epfl-dlab/aiflows/tree/main/examples/minimal%20reverse%20number/) and can be executed as follows:

```bash
cd examples/minimal\ reverse\ number/
python reverse_number_sequential.py
```

Upon running, the answer you should expect is:
```
[{'output_number': 1234}]
```
___


**Next Tutorial:** [Introducing the FlowVerse with a Simple Q&A Flow](./intro_to_FlowVerse_minimalQA.md)