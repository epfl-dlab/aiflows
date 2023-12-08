from copy import deepcopy
from typing import List, Dict
from aiflows.messages import Message


class FlowHistory:
    """
    Represents a history of messages.

    Attributes:
        messages (List[Messages]): A list of the messages comprising the history of a flow.
    """

    def __init__(self):
        self.messages: List[Message] = []

    def add_message(self, message: Message) -> None:
        """
        Adds a message to the history.

        :param message: The message to add.
        :type message: Message
        """
        self.messages.append(deepcopy(message))

    def get_last_n_messages(self, n: int) -> List[Message]:
        """
        Returns a list representation of the last n messages in the history.

        :param n: The number of messages to return.
        :type n: int
        :return: The list representation of the last n messages in the history.
        :rtype: List[Message]
        """
        return [m for m in self.messages[-n:]]

    def to_string(self) -> str:
        """
        Returns a string representation of the history.

        :return: The string representation of the history.
        :rtype: str
        """
        text = "\n".join([message.to_string() for message in self.messages])
        return text

    def to_list(self) -> List[Dict]:
        """
        Returns a list representation of the history.

        :return: The list representation of the history.
        :rtype: List[Dict]
        """
        return [m.to_dict() for m in self.messages]

    # def to_dict(self):
    #     return {"history": [m.to_dict() for m in self.messages]}

    def __len__(self):
        """Returns the length of the message history.

        :return: The length of the history.
        :rtype: int
        """
        return len(self.messages)

    def __str__(self):
        """Returns a string representation of the history.

        :return: The string representation of the history.
        :rtype: str
        """
        return self.to_string()

    # def __repr__(self):
    #     return repr(self.messages)
