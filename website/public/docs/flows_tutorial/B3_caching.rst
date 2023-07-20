.. _caching:

====================================
Understand the Caching Mechanism
====================================

To enable caching for a specific flow, you can decorate the Flow's ``run()`` method with the ``flow_run_cache()`` decorator. Note that caching the ``AtomicFlow``s, which actually perform the costly calls, is sufficent for reaping the benefits. If your ``AtomicFlow`` supports caching, you should set the class variable ``SUPPORTS_CACHING`` to ``True``.

Here's an example

..  code-block:: python

    from flows import Flow
    from flows.caching import flow_run_cache

    class MyFlow(Flow):
        # Flow implementation goes here
        SUPPORTS_CACHING=True
        
        @flow_run_cache()
        def run(self,
                input_data: Dict[str, Any],
                private_keys: Optional[List[str]] = [],
                keys_to_ignore_for_hash: Optional[List[str]] = []) -> Dict[str, Any]:
            # Flow logic with caching enabled
            pass

By decorating the ``run()`` method with ``flow_run_cache()``, the flow execution results will be cached based on the function parameters, the ``flow_config`` and ``flow_state``. Therefore, for the caching function to work correctly you need to make sure that **all parameters that could affect the computation** are contained in the ``flow_state``.

User should set env variable ``FLOW_DISABLE_CACHE`` to disable the cache globally.
