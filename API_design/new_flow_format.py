from typing import Dict, Any, Tuple, List, Union


class Message:
    pass


class Flow:
    state: Dict[str, Any]
    msg_history: List[Message]  # also includes log messages

    # let's assume the history can only every be appended to

    def update_state(self, data: Union[Dict[str, Any], Message], keys: List[str] = None):
        pass

    def log_message(self, message: Message):
        pass

    # ToDo: store state and history as one object? Disentangle when loading?
    def load(self, state, msg_history):
        # state must be a dict that can be serialized (pickle? JSON?)
        self.state = state
        self.msg_history = msg_history

    def store(self):
        return self.state, self.msg_history

    def step(self):
        new_state = None
        self.state = new_state

    @classmethod
    def initialize(cls, data: Dict[str, Any] = None) -> Tuple[Dict[str, Any], List[str]]:
        # reset state and history
        # if history is a part of state, then it's as easy as resetting state
        # initialization should be independent of a run() call
        pass

    # ToDo: make it clear: users can either implement step (maps state to state) or run(map TaskMessage to OutputMessage)

    @classmethod
    def step(cls, state, logs, msg_history):
        # update the flow by one step
        # return new_state, new_logs, new_history, finished
        return {}, [], [], False

    # add package_output method, but call it something better
    # on_finish ?

    # ToDo: this should probably not be in a flow, instead move it to a flow runner
    # just having it here to demonstrate the idea
    @classmethod
    def run(cls, taskMessage: TaskMessage):

        # how does this interact with caching / resuming?

        # log task message
        # update state from taskMessage.data, this will log a StateUpdateMessage
        # check validity (maybe before, first thing)

        # after the run is completed, the expectedOutputs must be keys in the state
        expected_outputs = taskMessage.expectedOutputs

        # initialize the flow from the data in TaskMessage
        # run until complete and return an OutputMessage

        while True:
            state, logs, msg_history, finished = cls.step(state, logs, msg_history)
            if finished:
                break
        return state, logs, msg_history


taskMessage = TaskMessage(data=resume_from_state, expectedOutputs=["a", "b"])
flow.run(taskMessage)
# -> updates the flow state from the task message

taskMessage = TaskMessage(expectedOutputs=["a", "b"])
flow.update_state_from_data(data={"code": "print('hi')"})
flow.run(taskMessage)
