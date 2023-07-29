.. _write_composite:

=========================
Composite Flow
=========================

The ``CompositeFlow`` class is a subclass of the ``Flow`` that orchestrates the collaboration between multiple atomic and/or composite subflows. It contains one key attribute in addition to the ones in the ``AtomicFlow``:

* ``subflows``: A dictionary that stores the subflows of the Flow.

Methods

* ``_call_flow_from_state(self, flow_to_call: Flow)``: A helper method that prepares the ``InputMessages``, calls a specific subflow, and handles the ``OutputMessage``.
* ``_set_up_subflows(cls, config)``: A class method that sets up the subflows of the `CompositeFlow.` It can be overridden if the initialization requires it. 
* ``run(self, input_data: Dict[str, Any]) -> Dict[str, Any]``: The main method that executes the logic of the Flow.

Like the ``AtomicFlow``, the ``CompositeFlow`` class is abstract and does not implement the ``run`` method. Subclasses of ``CompositeFlow`` should implement the ``run`` method to define the collaboration pattern of the subflows.

We currently provide two general patterns (to be extended): ``sequential`` and ``generator-critic``.

* ``Sequential``: The list of subflows is executed sequentially.
* ``GeneratorCritic``: The generator and the critic are called alternatingly for a specific number of rounds. 


Write a Composite Flow
========================

Writing a Composite Flow is even easier than writing an Atomic Flow --- the task is only to define the interface and the "flow" of the collaboration.

Define the Subflows
-------------------

Let's continue with the example of the ``ReverseNumberAtomicFlow`` and write a composite flow that reverses a number and then reverses the already reversed number.

Let's think about the message passing that should happen between the subflows. The task of the Sequential Flow is to start with ``number = 1234`` in the ``input_message``, and get the number reversed twice as part of the output message. We specify this behavior by:

..  code-block:: yaml

  name: "ReverseNumberTwice"
  description: "A sequential flow that reverses a number twice."

  input_data_transformations: []
  input_keys:
    - "number"

  output_data_transformations:
    - _target_: flows.data_transformations.KeyCopy
      old_key2new_key:
        raw_response.output_number: "output_number"
  output_keys:
    - "output_number"
  keep_raw_response: False  # Set to True to keep the raw flow response in the output data

The first subflow will get the ``input_number`` and reverse it, while the second subflow will take it's output and reverse it again. We specify this behavoir as:

..  code-block:: yaml

  subflows_config:
    - _target_: reverse_number_atomic.ReverseNumberAtomicFlow.instantiate_from_default_config
      overrides:
        name: "ReverseNumberFirst"
        description: "A flow that takes in a number and reverses it."

        input_data_transformations: [ ]
        input_keys:
          - "number"

        output_data_transformations:
          - _target_: flows.data_transformations.KeyCopy
            old_key2new_key:
              raw_response.output_number: "first_reverse_output"
        output_keys:
          - "first_reverse_output"
        keep_raw_response: False
    - _target_: reverse_number_atomic.ReverseNumberAtomicFlow.instantiate_from_default_config
      overrides:
        name: "ReverseNumberSecond"
        description: "A flow that takes in a number and reverses it."

        input_data_transformations:
          - _target_: flows.data_transformations.KeyRename
            old_key2new_key:
              first_reverse_output: "number"
        input_keys:
          - "number"

        output_data_transformations:
          - _target_: flows.data_transformations.KeyCopy
            old_key2new_key:
              raw_response.output_number: "output_number"
        output_keys:
          - "output_number"
        keep_raw_response: False

We pass this configuration to a ``SequentialFlow`` and we're done!

You can the complete implementatino for this example `here <https://github.com/epfl-dlab/flows/tree/main/tutorials/minimal_reverse_number>`__. For many more examples of ``CompositeFlows`` used for competitive coding see `this repository <https://huggingface.co/martinjosifoski/CC_flows>`__.
