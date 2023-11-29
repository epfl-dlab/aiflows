.. _write_atomic_old:

=========================
Write an Atomic Flow
=========================
There are two ways of creating your own ``Flow``.
You can derive from one of the abstract base classes and implement the ``run`` method.
Or you can use one of the highly flexible ``Flow`` classes from the Flow-verse and tweak their behaviour by modifying a yaml configuration file.

Let's start by implementing a simple ``Flow`` that plays rock-paper-scissors.

The RockPaperScissorsPlayer
----------------------------

Creating your own ``Flow`` takes just a few lines of code.
You derive from ``AtomicFlow`` and override the ``run`` `method <https://github.com/epfl-dlab/flows/blob/a41c55c38ea4111a88257c25dbac0344f8c59381/flows/base_flows/abstract.py#L378>`_.
Your ``run`` implementation needs to accept a dictionary with ``input_data``.
Optional paramters are ``private_keys`` and ``keys_to_ignore_for_hash``.
For now, only the ``input_data`` is important::

    from flows.base_flows.abstract import AtomicFlow

    class RockPaperScissorsPlayer(AtomicFlow):

        def __init__(self, **kwargs):
            super(RockPaperScissorsPlayer, self).__init__(**kwargs)

        def run(self, input_data, expected_outputs: List[str] = None):
            assert expected_outputs ==["choice"], "RockPaperScissorsPlayer only has one output: choice"
            choice = random.choice(["rock", "paper", "scissors"])
            return {"choice": choice}

The constructor of your new ``Flow`` must call the constructor of the base class, passing all the arguments received in ``**kwargs``.
When creating an instance of a ``Flow``, all arguments will be stored in ``flow_config``.
At the least, you must pass a ``name`` and ``description``::

    player = RockPaperScissorsPlayer(name="Player A", description="RockPaperScissorsPlayer")
    print(player.flow_config)

``Flow`` instances communicate by sending each other messages.
All messages are instances of the abstract ``Message`` base class.
There are three special messages:

* ``TaskMessage``: when a ``Flow`` instance receives a ``TaskMessage``, it's ``run`` method is called.
* ``OutputMessage``: the results of ``run`` are packaged in an ``OutputMessage`` and returned to the calling ``Flow``.
* ``StateUpdateMessage``: every update of the state of a flow should be logged with a ``StateUpdateMessage``.


Don't worry, you don't have to create these messages yourself.
The ``Flow`` base classes provides convenient methods to create them for you.
The messaging system serves two important purposes (both will be explained in advanced tutorials):

* Caching is based on the hash of a ``flow_state`` and ``TaskMessage``.
* We provide a visualization toolkit that helps you debug the history of a ``Flow`` instance, by showing the Messages that were sent and received.

For now, let's see how you can use the convenience methods to run your new ``RockPaperScissorsFlow``::

    # a TaskMessage contains
    # - the recipient flow
    # - a description of the task
    # - input data
    # - a list of expected outputs
    task_message = player.package_task_message(player, "play one round", {}, expected_outputs=["choice"])
    output = player(task_message)

    # as a response to a task, a flow will send an OutputMessage
    # it contains metadata about the task execution, as well as results
    print(output.data['choice'])
