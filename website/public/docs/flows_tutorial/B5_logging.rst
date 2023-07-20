.. _logging:

=======
Logging
=======

The logging level is set to ``INFO`` by default. 

To change the default logging level, you can set the ``LOGGING_LEVEL`` environment variable to one of the following values: ``DEBUG``, ``INFO``, ``WARNING``, ``ERROR``, ``CRITICAL``; or by including the following snippet in your code.

..  code-block:: python

    from flows import logging
    logging.set_verbosity_debug()
