import copy
from typing import List, Union, Dict
from src.messages import Message


class FlowHistory:
    """
    Represents a history of messages.

    Attributes:
        messages (List[ms.Message]): A list of messages in the history.

    Methods:
        add_message: Adds a message to the history.
        get_messages_by: Retrieves messages by the target message creator.
        remove_messages: Removes messages using a list of message IDs
        get_latest_message: Returns the latest message
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

    def get_chat_messages(self) -> List[Message]:
        from src.messages import ChatMessage
        return [m for m in self.messages if isinstance(m, ChatMessage)]

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

    def to_list(self) -> List[Dict]:
        """
        Converts the history to a dictionary representation.

        Returns:
            dict: The dictionary representation of the history.
        """
        return [m.to_dict() for m in self.messages]

    def __len__(self):
        return len(self.messages)

    def __str__(self):
        return self.to_string()

    def __repr__(self):
        return repr(self.messages)
