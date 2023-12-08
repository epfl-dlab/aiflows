from abc import ABC

from aiflows.base_flows import Flow


class AtomicFlow(Flow, ABC):
    """
    AtomicFlow is the minimal execution unit in the Flow framework.
    It is an encapsulation of a single functionality that takes an input message and returns an output message.

    :param \**kwargs: Arguments to be passed to the Flow constructor
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @classmethod
    def type(cls):
        """Returns the type of the flow."""
        return "AtomicFlow"
