from abc import ABC

from flows.base_flows import Flow


class AtomicFlow(Flow, ABC):
    """
    AtomicFlow is the minimal execution unit in the Flow framework.
    It is an encapsulation of a single functionality that takes an input message and returns an output message.
    """

    def __init__(
            self,
            **kwargs
    ):
        super().__init__(**kwargs)

    @classmethod
    def type(cls):
        return "AtomicFlow"
