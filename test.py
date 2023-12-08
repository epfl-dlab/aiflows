dependencies = [
    {"url": "nbaldwin/ChatInteractiveFlowModule", "revision": "main"},
]
from flows import flow_verse
flow_verse.sync_dependencies(dependencies)

from flow_modules.nbaldwin.ChatInteractiveFlowModule import ChatHumanFlowModule

if __name__ == "__main__":
	print("This is a trivial sync demo.")