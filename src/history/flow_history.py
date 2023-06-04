import copy
from typing import List, Union
from src.messages import Message, FlowMessage


class History:
    """
    Represents a history of messages.

    Attributes:
        messages (List[ms.Message]): A list of messages in the history.

    Methods:
        add_message: Adds a message to the history.
        get_messages_by: Retrieves messages by the target message creator.
        to_string: Converts the history to a string representation.
        to_dict: Converts the history to a dictionary representation.
        __len__: Returns the number of messages in the history.
        __str__: Returns a string representation of the history.
    """

    def __init__(self):
        self.messages: List[Message] = []

    def add_message(self, message: Message) -> Message:
        """
        Adds a message to the history as deepcopy.
        It returns the deepcopied message.

        Args:
            message (Message): The message to add.

        Returns:
            Message: The added message.
        """
        new_ms = copy.deepcopy(message)
        self.messages.append(new_ms)
        return new_ms

    def get_messages_by(self, target_message_creator: str) -> List[Message]:
        """
        Retrieves messages by the target message creator.

        Args:
            target_message_creator (str): The target message creator.

        Returns:
            List[Message]: A list of messages created by the target message creator.
        """
        return [m for m in self.messages if m.message_creator == target_message_creator]

    def remove_messages(self, message_ids_to_remove: List[str]):
        """
        Removes messages from a list of message ids to remove.

        Args:
            message_ids_to_remove (List[str]): The IDs of the messages to be removed.
        """
        for message_id in message_ids_to_remove:
            message_to_remove = [m for m in self.messages if m.message_id == message_id]

            assert len(message_to_remove) == 1, \
                f"Error when trying to remove message with ID {message_id} from history {str(self)}"

            self.messages.remove(message_to_remove[0])

    def get_latest_message(self) -> Union[Message, None]:
        """
        Retrieves the latest message from the history.

        Returns:
            Message: The latest message in the history, or None is empty
        """
        if self.messages:
            return self.messages[-1]
        else:
            return None

    def to_string(self, messages: List[Message] = None, **kwargs) -> str:
        """
        Converts the history to a string representation.

        Args:
            messages (List[Message], optional): The messages to convert. Defaults to None.

        Returns:
            str: The string representation of the history.
        """
        if messages is None:
            messages = self.messages

        text = "\n".join([message.to_string(**kwargs) for message in messages])
        return text

    def to_dict(self) -> dict:
        """
        Converts the history to a dictionary representation.

        Returns:
            dict: The dictionary representation of the history.
        """
        return {"history": [m.to_dict() for m in self.messages]}

    def __len__(self):
        return len(self.messages)

    def __str__(self):
        return self.to_string()


class FlowHistory(History):
    """
    Represents a history of flow messages.

    Inherits from the History class.

    Attributes:
        messages (List[ms.FlowMessage]): A list of flow messages in the history.

    Methods:
        flow_run_ids: Returns a set of flow run IDs present in the history.
    """
    def __init__(self):
        super().__init__()
        self.messages: List[FlowMessage] = []

    @property
    def flow_run_ids(self):
        """
        Returns a set of flow run IDs present in the history.

        Returns:
            set: The set of flow run IDs.
        """
        return set([message.flow_run_id for message in self.messages])
