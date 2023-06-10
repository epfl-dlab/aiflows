from dataclasses import dataclass

from flows.messages import Message


@dataclass
class ChatMessage(Message):
    content: str

    def __init__(self, **kwargs):
        super(ChatMessage, self).__init__(**kwargs)
        self.content = kwargs.pop("content", None)
