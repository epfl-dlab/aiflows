# Composite Flow

The `CompositeFlow` class is a subclass of the `Flow` that orchestrates the collaboration between multiple atomic and/or composite subflows. 

The'CompositeFlow' class contains one key attribute in addition to the ones in the `AtomicFlow`:
- `subflows`: A dictionary that stores the subflows of the Flow.

Methods
- `_call_flow_from_state(self, flow_to_call: Flow)`: A helper method that prepares the InputMessages, calls a specific sub-flow, and handles the OutputMessage.
- `_set_up_subflows(cls, config)`: A class method that sets up the sub-flows of the `CompositeFlow.` It can be overridden if the initialization requires it. 
- `run(self, input_data: Dict[str, Any]) -> Dict[str, Any]`: The main method that executes the logic of the Flow.

Like the `AtomicFlow,` the `CompositeFlow` class is abstract and does not implement the `run` method. 
Subclasses of `CompositeFlow` should implement the `run` method to define the collaboration pattern of the sub-flows.
We currently provide two general patterns (to be extended): `sequential` and `generator-critic.`

- `Sequential`: The list of subflows is executed sequentially.
- `GeneratorCritic`: The generator and the critic are called alternatingly for a specific number of rounds. 

## Writing a Composite Flow

Writing a Composite Flow is even easier than writing an Atomic Flow -- the task is only to define the interface and the "flow" of the collaboration.

### Define the Subflows
Let's continue with the example of the `ReverseNumberAtomicFlow` and write a composite flow that reverses a number and then reverses the already reversed number.

Let's think about the interface of this flow. The task of the Sequential Flow is to start with `number=1234` in the `input_message`, and get the number reversed twice as part of the output message. We specify this interface as:
```yaml
name: "ReverseNumberTwice"
description: "A sequential flow that reverses a number twice."

input_interface:
  - "number"

output_interface:
  - "output_number"
```
Now we need to define the subflows which will be executed sequentially.
The frist sub-flow will get the input_number and reverse it, while the second sub-flow will take it's output and reverse it again. We specify this behavoir as:
```yaml
subflows_config:
  first_reverse_flow:
    _target_: reverse_number_atomic.ReverseNumberAtomicFlow.instantiate_from_default_config
    overrides:
      name: "ReverseNumberFirst"
      description: "A flow that takes in a number and reverses it."
  second_reverse_flow:
    _target_: reverse_number_atomic.ReverseNumberAtomicFlow.instantiate_from_default_config
    overrides:
      name: "ReverseNumberSecond"
      description: "A flow that takes in a number and reverses it."
```

At this stage, we have defined the interface and the subflows of our `CompositeFlow.` 
We now need to define the logic of the flow, i.e., how the subflows will be executed, i.e. the topology of the flow.
To do this, we need to define the `topology` attribute of the flow.
A single element of the topology is a dictionary that contains the following keys:
- `goal`: A string that describes the goal of the flow.
- `input_interface`: The interface of the input message of the flow and optionally a transformation of the input message.
- `flow`: The name of the subflow to be executed.
- `output_interface`: The interface of the output message of the flow and optionally a transformation of the output message.

In the case of the `ReverseNumberTwice` flow, we need to define two elements in the topology:

```yaml
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
      keys_to_rename:
        raw_response.output_number: output_number
      keys_to_select: ["output_number"]
```

You can the complete implementatino for this example [here](https://github.com/epfl-dlab/flows/tree/main/tutorials/minimal_reverse_number). For many more examples of CompositeFlows used for competitive coding see [this](https://huggingface.co/martinjosifoski/CC_flows) repository.