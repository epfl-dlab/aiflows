flowverse_test:
	pytest tests/flow_verse/test_sync_dependencies.py -s

flowcache_test:
	pytest tests/flow_cache/test_flow_cache.py -s

test: flowverse_test flowcache_test
