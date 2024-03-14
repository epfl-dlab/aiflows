# ~~~ Specify the dependencies ~~~

dependencies = [
    {"url": "aiflows/ChatFlowModule", "revision": "main"}
]
# Revision can correspond toa branch, commit hash or a absolute path to a local directory (ideal for development)
from aiflows import flow_verse

flow_verse.sync_dependencies(dependencies)

# ~~~ Import of your flow class (if you have any) ~~~
# from .NAMEOFYOURFLOW import NAMEOFYOURFLOWCLASS
from .SamplerFlow import SamplerFlow
