
# ~~~ Specify the dependencies ~~~
dependencies = [
    {"url": "aiflows/ChatInteractiveFlowModule", "revision": "main"},
]
from aiflows import flow_verse

flow_verse.sync_dependencies(dependencies)
