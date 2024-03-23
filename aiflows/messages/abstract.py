import copy
import json
from dataclasses import dataclass
from typing import List, Any, Dict
import colorama

from aiflows.utils.general_helpers import create_unique_id, get_current_datetime_ns
from aiflows.utils.io_utils import coflows_deserialize, coflows_serialize
colorama.init()


@dataclass
class Message:
    """This class represents a message that is passed between nodes in a flow.

    :param data: The data content of the message
    :type data: Dict[str, Any]
    :param created_by: The name of the flow that created the message
    :type created_by: str
    :param private_keys: A list of private keys that should not be serialized or logged
    :type private_keys: List[str], optional
    """

    # ~~~ Message unique identification ~~~
    message_id: str
    created_at: str

    # ~~~ Contextual information about the message ~~~
    created_by: str
    message_type: str

    # ~~~ Data content ~~~
    data: Dict[str, Any]

    # ~~~ Private keys that should not be serialized or logged ~~~
    private_keys: List[str]

    def __init__(self, data: Dict[str, Any], created_by: str, private_keys: List[str] = None):

        # ~~~ Initialize message identifiers ~~~
        self.message_id = create_unique_id()
        self.created_at = get_current_datetime_ns()

        # ~~~ Initialize contextual information ~~~
        self.message_type = self.__class__.__name__
        self.created_by = created_by

        # ~~~ Initialize Data content ~~~
        self.data = data

        # ~~~ Initialize private keys ~~~
        self.private_keys = [] if private_keys is None else private_keys

    def _reset_message_id(self):
        """Resets the message's unique identification (message_id,created_at)"""
        self.message_id = create_unique_id()
        self.created_at = get_current_datetime_ns()

    def __sanitized__dict__(self):
        """Removes any private_keys potentially present in the __dict__ object or the data dictionary"""
        __sanitized__dict__ = copy.deepcopy(self.__dict__)

        for private_key in self.private_keys:
            if private_key in __sanitized__dict__:
                del __sanitized__dict__[private_key]

        for private_key in self.private_keys:
            if private_key in __sanitized__dict__["data"]:
                del __sanitized__dict__["data"][private_key]

        del __sanitized__dict__["private_keys"]
        return __sanitized__dict__

    def to_dict(self):
        """Returns a dictionary representation of the message that can be serialized to JSON"""
        d = self.__sanitized__dict__()
        return d

    def to_string(self):
        """Returns a formatted string representation of the message that will be logged to the console"""
        raise NotImplementedError()

    def __str__(self):
        """Returns a string representation of the message that can be logged to the console"""
        d = self.__sanitized__dict__()
        return json.dumps(d, indent=4, default=str)
    
    def serialize(self):
        """ Returns the serialized message
        
        :return: The serialized message
        :rtype: bytes
        """
        return coflows_serialize(self.to_dict())

    @classmethod
    def deserialize(cls, encoded_data: bytes):
        """ Deserializes the encoded data into a message
        
        :param encoded_data: The encoded message 
        :type encoded_data: bytes
        :return: The deserialized message
        :rtype: Message
        """
        d = coflows_deserialize(encoded_data)
            
        message_id = d.pop("message_id")
        created_at = d.pop("created_at")
        message_type = d.pop("message_type")
    
        msg = cls(**d)
        msg.message_id = message_id
        msg.created_at = created_at
        assert msg.message_type == message_type,"Message type mismatch"
        return msg

        
