from dataclasses import dataclass
from typing import Dict, Any, Tuple, List


# all messages should have a data dictionary
# for chat messages, we can make this data = {"content": "hello world"}
@dataclass
class Message:
    # id, creator, created_at, ...

    # all message should contain a data dict
    # for chat messages, this can contain data.content
    data: Dict[str, Any]

# OutputMessages are a special message
# their data field contains the output that the flow wants to pass out
# they also record success/failure, and the history of the flow, as well as the final state
@dataclass
class OutputMessage(Message):
    success:bool
    error_message: None | str
    history: Any
    flow_state: Dict[str, Any]

# the state of a flow can be updated from a data dict or other messages
# to log that an update has occured we use this special message
@dataclass
class StateUpdateMessage(Message):
    keys_updated: Dict[str, Any]
    source_message: Dict[str, Any]

@dataclass
class Flow:
    # history, etc

    # the state of the flow is now a data dictionary
    state: Dict[str, Any]

    # we should keep track where an entry in the state is coming from
    # to do this, we store the ID of a message in another dictionary
    # state["code"] was created by message with ID source_message["code"]
    source_message: Dict[str, str]

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