from dataclasses import dataclass
from typing import Dict, Any, Tuple, List


@dataclass
class Message:
    # id, creator, created_at, ...
    message_id: str
    message_creator: str
    created_at: str
    parent_message_ids: List[str] # rename parents 
        
    flow_runner: str
    flow_run_id: str
        
    # all messages should have a data dictionary
    # for chat messages, we can make this data = {"content": "hello world"}
    data: Dict[str, Any]

    # ToDo: these two extra fields could be useful for visualization
    # The name would be displayed in the message header
    # after "expanding" the message, we see the description
    # but this is a minor detail and not related to the rest of the proposal
    name: str
    description: str

# We could create a ParsingMessage which is meant to be used in combination with ChatModel messages
# it looks at the raw text in data.content and parses it into a data dictionary
# I would argue against this: I think this shouldn't be a new message class, the existing dataclass can handle it:
# 1. Message with data = {content: "```python\nprint('hello world')\n```"}
# 2. Message with data = {code: "print('hello world')", parsing_success:True}

# There are special types of messages

# OutputMessage
# their data dictionary contains the output that the flow wants to pass out
# they also record success/failure, and the history of the flow, as well as the final state
@dataclass
class OutputMessage(Message):
    success:bool
    error_message: None | str
    history: Any
    flow_state: Dict[str, Any]

# StateUpdateMessage, replaces InputMessage
# the state of a flow can be updated from a data dict or other messages
# to log that an update has occurred we use this special message
# an example history could look like this
# 1. Message with data = {content: "```python\nprint('hello world')\n```"}
# 2. Message with data = {code: "print('hello world')", parsing_success:True}
# 3. StateUpdateMessage with data = {code: "print('hello world')"}, source_message points to the previous message
#
# Note: the StateUpdateMessage does not reproduce all fields from the previous message
# deciding what to put in the state update is the job of the flow
# here we see that the parsing was successful and therefore decide to put the code in the state
# if the parsing was not successful, we'd probably not update the state at all
# or we could create a message like this
# 3(b). StateUpdateMessage with data = {num_failed_attempts: 1}, source_message points to the StateUpdateMessage itself
@dataclass
class StateUpdateMessage(Message):
#     keys_updated: List[str] , either we keep just the key or the data
    updates: Dict[str, Any]

@dataclass 
class TaskMessage(Message):
    expected_output_keys: List[str] 
    # With default in-filling for Message fields if they are not set, so that we do:
    # flow.run(TaskMessage(data={}))
    
# the Flow class has helper methods to produce StateUpdateMessages and OutputMessages
@dataclass
class Flow:
    # history, etc

    # the state of the flow is now a data dictionary
    state: Dict[str, Any]

    # we should keep track where an entry in the state is coming from
    # to do this, we store the ID of a message in another dictionary
    # state["code"] was created by message with ID source_message["code"]
#     source_message: Dict[str, str]

    def update_state_from_data(self, data: Dict[str, Any], keys:List[str]=None):
        # merge the data dictionary into the state
        # if keys is given, use only those keys
        # log a StateUpdateMessage
        # the source_message in the StateUpdateMessage points to the StateUpdateMessage itself
        pass

    # when receiving data
    def update_state_from_message(self, message:Message, keys:List[str]=None):
        # merge the message data into the state
        # if keys is given, use only those keys
        # log a StateUpdateMessage
        # the source_message in the StateUpdateMessage points to message
        pass

    # ToDo: we could allow updating the state from multiple messages at once
    # for example like this:
    def update_state_from_messages(self, messages: List[Message], keys:List[str]=None):
        # merge the data dicts of all messages into the state
        # if keys is given, use only those keys
        # log one StateUpdateMessage which includes all the updated keys in the state
        pass

    # previously we had expected_inputs_given_state()
    # this method was used to validate an input message
    # but now we allow the user to feed data into the state, either from a data dict, or from a message
    # possibly, the user wants to update the state in more than one step,
    # reading input from multiple messages and data dicts
    # therefore we now have a separate method for validating the state
    def assert_state_valid(self) -> bool:
        # check if all expected keys are in the state
        pass

    def run(self):
        self.assert_state_valid()
        # run the flow
        # ...

    def package_output_message(self, expected_outputs: List[str] = None) -> OutputMessage:
        if expected_outputs is not None:
            output_fields = expected_outputs
        else:
            output_fields = self.expected_outputs

        # assert that all output fields are in the state
        # create an OutputMessage with these fields
