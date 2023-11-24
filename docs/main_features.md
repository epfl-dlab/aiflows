# Main Features

## Flow

The `Flow` class is an abstract class (ABC) that is the basis for all flows.
It defines the shared structure and behavior, such as managing the configuration, state, history, and, crucially, the standardized interface. 

The `Flow` class contains the following key attributes and methods:

### Attributes
- `flow_config`: A dictionary completely specifying the Flow. Calling the `instantiate_from_config` with the `flow_config` should lead to an equivalent Flow object.
- `flow_state`: A dictionary containing all the information that affects the Flow's computation. For instance, for a chat model, the previous messages would be part of the flow_state.
- `history`: An instance of the `FlowHistory` class that tracks the history of `Message` objects sent and received by the Flow. The history logs the complete computation graph of the Flow.

### Core Methods
- `instantiate_from_config(cls, flow_config: Dict[str, Any]) -> Flow`: A class method that instantiates a flow from a configuration dictionary. This method is the recommended way of instantiating a flow.
- `__call__(self, input_message: InputMessage) -> OutputMessage`: The method that executes the logic of the Flow. This method is the entry point for the Flow when passing an input message (i.e., for communication between Flows). Note that the recommended entry point for starting a flow run with a data dictionary is the `FlowLauncher` class.
- `set_up_flow_state(self)`: A method that sets up the initial `flow_state` attribute for a Flow. This method is called by the `__init__` method and/or the reset function to `factory reset` the Flow. Subclasses of `Flow` often override this function to achieve a specific behavior.
- `get_interface_description(self)`: The interface contains two keys: `input` and `output`. Each key contains a list of dictionaries, each of which describes a list of strings that are the names of the variables in the input and output data dictionaries. 
- `package_output_message(self, input_message: InputMessage, response: Any) -> OutputMessage`: A method that packages the flow response into an `OutputMessage` object based on the "task_definition" specified in the `InputMessage.` 
- `reset(self, full_reset: bool, recursive: bool)`: A method that clears only the Flows namespace (if `full_reset` is false) -- this is done at the end of every call by default (a behavior that can be overridden) -- or the `flow_state` as well (if `full_reset` is true).


### FlowLauncher

```python
class FlowLauncher:
    @staticmethod
    def launch(flow_with_interfaces: Dict[str, Any], data: Union[Dict, List[Dict]], path_to_output_file: Optional[str] = None, api_keys: Optional[Dict[str, str]] = None) -> Tuple[List[dict]]:
```

The FlowLauncher is the entry point for running a flow on a sample (or a list of samples).

The `launch` method encapsulates the following steps:
- Packages the data into an `InputMessage` object.
- Runs the Flow on the `InputMessage` object.
- Records the outputs and (optionally) saves them to file
- Resets the flow state at each iteration.

Note that this is the simple launcher. The same [file](https://github.com/epfl-dlab/flows/blob/main/flows/flow_launchers/flow_API_launcher.py) also contains the FlowAPILauncher which requires more parameters but at the same time supports more features, such as multithreading which can trivially speed-up your experiments to the maximum allowed by your API rate limits.

### Flow Config

`flow_config` is a dictionary containing everything necessary to instantiate the Flow by running `instantiate_from_config .`It has the following mandatory keys:
  - `name`: The name of the Flow.
  - `description`: A description of the Flow.
  - the parameters specifying the interface of the Flow (by default, these are the `input_keys` and `output_keys`)
  - other parameters necessary to instantiate a flow object (e.g., `generation_params` or `prompt_templates`)

### Flow State

`flow_state` is a dictionary containing all the information that affects the Flow's computation.
Flows are, generally, stateful operators. The `flow_state` stores the intermediate results of the current execution and any information that can affect future computations resulting from prior runs. 
This object is handy for coordinating computation spanning multiple rounds or involving numerous flows. 
A standard example of a stateful Flow is `ChatAtomicFlow,` which has the `previous_messages` as part of its `flow_state.` 

The `flow_state` is initialized by the `set_up_flow_state` method of the `Flow` class.
The `flow_state` can be reset by calling the `reset` method of the `Flow` class. By default, the `reset` method is called by the `FlowLauncher` class at the end of the execution for each data sample to ensure a clean state before running the next one. Some use cases might require a `reset` even within a single run.

### Message
The `Message` class is a data object representing the basis of the communication between flows. There are three general types of messages:
an `InputMessage` that can be seen as a task definition
an `OutputMessage` that corresponds to the result of a task execution
and `UpdateMessage` that logs any changes to the flow state during the execution
Depending on the nature of the update, different subtypes of `UpdateMessage` are defined (and can be extended), but they all serve the same purpose.
The `Message` class contains data and metadata. See the `flows/messages/flow_message.py` for details.

### Flow History
The `history` attribute constitutes a list of `Message` objects. The list is extended via the `_log_message` method of the `Flow` class.
It is an instance of the `FlowHistory` class that tracks the complete computation graph of a Flow run.