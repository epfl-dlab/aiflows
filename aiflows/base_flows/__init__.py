"""
Contains basic flow classes that can be used to build more complex flows.

AtomicFlow is the minimal execution unit in the Flow framework.
CompositeFlow is a flow that contains subflows and defines how they are executed.
"""

from .abstract import Flow
from .atomic import AtomicFlow
from .composite import CompositeFlow

