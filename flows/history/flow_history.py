from typing import List, Dict
from flows.messages import Message


class FlowHistory:
    """
    Represents a history of messages.

    Attributes:
        messages (List[Messages]): A list of the messages comprising the history of a flow.

    Methods:
        add_message: Adds a message to the history.
        to_string: Returns a string representation of the history.
        to_list: Returns a list representation of the history.
        to_dict: Returns a dict representation of the history.
        __len__: Returns the number of messages in the history.
        __str__: Returns a string representation of the history.
    """

    def __init__(self):
        self.messages: List[Message] = []

    def add_message(self, message: Message) -> None:
        """
        Adds a message to the history.

        Args:
            message (Message): The message to add.
        """
        self.messages.append(message)

    def to_string(self) -> str:
        """
        Returns a string representation of the history.

        Returns:
            str: The string representation of the history.
        """
        text = "\n".join([message.to_string() for message in self.messages])
        return text

    def to_list(self) -> List[Dict]:
        """
        Returns a list representation of the history.

        Returns:
            list: The list representation of the history.
        """
        return [m.to_dict() for m in self.messages]

    # def to_dict(self):
    #     return {"history": [m.to_dict() for m in self.messages]}

    def __len__(self):
        return len(self.messages)

    def __str__(self):
        return self.to_string()

    # def __repr__(self):
    #     return repr(self.messages)
