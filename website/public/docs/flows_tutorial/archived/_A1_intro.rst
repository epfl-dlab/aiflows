=========================
Getting started tutorial
=========================

This guide helps you implement two simple flows that play a game of Rock-Paper-Scissors.
You can find the full source code `here <https://github.com/epfl-dlab/flows/tree/working_e2e_flows/tutorials/rock_paper_scissors/>`_.

-----------------------------
Implement a simple ``Flow``
-----------------------------
Creating your own ``Flow`` takes just a few lines of code. You need to derive from one of the abstract base classes and implement a ``run`` method.

The ``run`` method receives a dictionary with ``input_data``, as well as a list of ``expected_outputs``.
It must return a dictionary that contains all the values in ``expected_outputs`` as keys::

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

----------------------------
Implement a nested ``Flow``
----------------------------

Now that we have a flow that can choose a random move, let's orchestrate a whole game of Rock-Paper-Scissors.
We will implement a ``RockPaperScissorsJudge`` that runs 3 rounds of Rock-Paper-Scissors between two players.

This ``Flow`` helps us to introduce the concept of ``flow_state``.
The parameters of the constructor of a ``Flow`` are stored in ``flow_config``.
The ``flow_state`` is a dictionary which contains all data that describes the current state of a ``Flow``.
You can set an initial state, by overriding the ``initialize`` method. It is called by the constructor of ``Flow``::

    class RockPaperScissorsJudge(Flow):

        def __init__(self, **kwargs):
            super(RockPaperScissorsJudge, self).__init__(**kwargs)

        def initialize(self):
            # use flow_state to store the state of the flow
            self.flow_state["A"] = RockPaperScissorsPlayer(name="Player A", description="RockPaperScissorsPlayer")
            self.flow_state["B"] = RockPaperScissorsPlayer(name="Player B", description="RockPaperScissorsPlayer")
            self.flow_state["A_score"] = 0
            self.flow_state["B_score"] = 0
            self.flow_state["n_rounds_played"] = 0

Now, when you create an instance of ``RockPaperScissorsJudge``, it will populate the state with a valid initial state::

    judge = RockPaperScissorsJudge(name="Judge", description="RockPaperScissorsJudge")
    print(judge.flow_state["n_rounds_played"]) # prints 0

You can write to the ``flow_state`` directly, but we also offer a convenience method, which automatically logs a ``StateUpdateMessage``: ``self._update_state``.
When you implement ``run``, you should use this method to log all important changes to the state.
Here is how we implement ``run`` for ``RockPaperScissorsJudge``. It uses task messages to get choices from the two players and updates its state based on the result of the round::

    def run(self, input_data, expected_outputs) -> Dict:
        # the run method can include any logic you want
        # including calls to other flows
        flow_a = self.flow_state["A"]
        flow_b = self.flow_state["B"]

        # play 3 rounds of rock paper scissors
        for _ in range(3):

            # both player flows are called with a task message
            A_task = self.package_task_message(flow_a, "run", {}, expected_outputs=["choice"])
            A_output = flow_a(A_task)
            self._log_message(A_output)
            A_choice = A_output.data["choice"]

            B_task = self.package_task_message(flow_b, "run", {}, expected_outputs=["choice"])
            B_output = flow_b(B_task)
            self._log_message(B_output)
            B_choice = B_output.data["choice"]

            # you can change the state of the flow by writing to self.flow_state
            # if you use the _update_state method, a StateUpdateMessage message will be logged
            self._update_state({"n_rounds_played": self.flow_state["n_rounds_played"] + 1})

            if A_choice == B_choice:
                # neither has won
                pass
            elif (A_choice == "rock" and B_choice == "scissors"
                  or A_choice == "paper" and B_choice == "rock"
                  or A_choice == "scissors" and B_choice == "paper"):
                self._update_state({"A_score": self.flow_state["A_score"] + 1})
            else:
                self._update_state({"B_score": self.flow_state["B_score"] + 1})

        # at the end of run, you need to return a dictionary which has the expected outputs as keys
        # we offer a concenience method to extract the corresponding values from the flow_state
        return self._get_keys_from_state(expected_outputs, allow_class_namespace=False)

Now that we have a complete implementation of both the judge and the players, let's see who wins a game of Rock-Paper-Scissors::

    judge = RockPaperScissorsJudge(name="RockPaperScissorsJudge", description="RockPaperScissorsJudge")
    task = judge.package_task_message(judge, "run", {}, expected_outputs=["A_score", "B_score"])
    output = judge(task)

    print(f"player A won {output.data['A_score']} rounds")

----------------------------
State management
----------------------------

``Flow`` instances embrace a functional programming paradigm. This is essential to enable our caching mechanism and it prevents side effects that can't be recorded by the ``StateUpdateMessage`` logs.

When processing a task message with ``player(task_message)``, the ``Flow`` instance will log the ``task_message``, call ``run`` and package the results as an ``OutputMessage``.
It also calls ``reset(full_reset=False)`` to clean all data which is not stored in ``flow_state``.
This means that during ``run`` you can store temporary data in instance attributes, such as ``self.temp = 1``,
but you should not expect this data to be available in the next call to ``run``.
After reset, the only instance attributes are the parameters stored in ``flow_config``.
All persistent data must be stored in ``flow_state``::

    judge = RockPaperScissorsJudge(name="RockPaperScissorsJudge", description="RockPaperScissorsJudge")
    print(f"In the beginning, the judge has seen a total of {judge.flow_state['n_rounds_played']} rounds")

    # after executing a task, the flow_state is automatically reset
    judge._temp = 0
    task = judge.package_task_message(judge, "run", {}, expected_outputs=["A_score", "B_score", "n_rounds_played"])
    output = judge(task)
    print(f"After one task, the judge has seen a total of {judge.flow_state['n_rounds_played']} rounds")

    # an Exception is thrown if you try to access an attribute that was deleted by reset
    try:
        print(judge._temp)
    except AttributeError:
        print("_temp was deleted by reset") # prints "_temp was deleted by reset"


If you want to perform a full reset of the flow instance, you can call ``reset()``.
This will reset both instance attributes and ``flow_state``. Then it calls ``initialize`` to set the initial state::

    judge.reset()
    print(f"After resetting, the judge has seen a total of {judge.flow_state['n_rounds_played']} rounds") # prints 0

