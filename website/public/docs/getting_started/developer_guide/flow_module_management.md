# Flow Module Management

### By the Tutorial's End, I Will Have...

* Gained a clear understanding of pulling flows from the FlowVerse.

* Mastered the handling of flows that depend on other flows.

## Introduction

The FlowVerse is a repository of Flows (powered by the 🤗 HuggingFace hub) created and shared by our community for everyone to use! With aiFlows, these Flows can be readily downloaded, used, extended or composed into novel, more complex Flows. For the ones using ChatGPT, you could think of them as open-source GPTs(++). 

In the heart of this platform, the community shares their unique Flows, encapsulated in what we call **flow modules**.

## Flow Modules

- Each Hugging Face published repository corresponds to a self-contained flow module. For instance, [nbaldwin/ChatInteractiveFlowModule](https://huggingface.co/nbaldwin/ChatInteractiveFlowModule) is a flow module.
- A module may include multiple Flow classes and potentially a default configuration YAML file. In the [nbaldwin/ChatInteractiveFlowModule](https://huggingface.co/nbaldwin/ChatInteractiveFlowModule) module, you can find [ChatHumanFlowModule.py](https://huggingface.co/nbaldwin/ChatInteractiveFlowModule/blob/main/ChatHumanFlowModule.py).
- Each Flow class can depend on other remote, publicly available modules. For example, [ChatHumanFlowModule.py](https://huggingface.co/aiflows/ChatInteractiveFlowModule/blob/main/ChatHumanFlowModule.py) depends on [aiflows/ChatFlowModule](https://huggingface.co/aiflows/ChatFlowModule).

## Syncing Flow Modules

To use or import a flow module, first sync it to the `flow_modules` directory in your root directory. You can then import it like any local Python package. Consider the following `trivial_sync_demo.py`, which relies on [nbaldwin/ChatFlows](https://huggingface.co/nbaldwin/ChatInteractiveFlowModule):

```python
dependencies = [
    {"url": "nbaldwin/ChatInteractiveFlowModule", "revision": "main"},
]
from aiflows import flow_verse
flow_verse.sync_dependencies(dependencies)

from flow_modules.nbaldwin.ChatInteractiveFlowModule import ChatHumanFlowModule

if __name__ == "__main__":
	print("This is a trivial sync demo.")
```

This synchronization process, though it may seem unconventional at first, provides a number of advantages:
* The synchronization process examines the implementation of remote flow modules seamlessly, eliminating the need to switch between your integrated development * environment (IDE) and a web page.
* It extends existing implementations effortlessly without the requirement to download or clone the repository manually.

## Flow Module Namespace

* Remote flow modules are identified by their Hugging Face repository ID and revision, such as `nbaldwin/ChatInteractiveFlowModule:main`.
* Each locally synchronized flow module manifests as a valid Python package within the `flow_modules` directory, exemplified by structures like `flow_modules.nbaldwin.ChatInteractiveFlowModule`. Importantly, only one revision is retained for each remote flow module, a practice upheld to ensure clarity and manage revision conflicts. Should a conflict arise, a warning will guide you to select the preferred version.

For a visual representation, consider the following directory structure:

```shell
(aiflows) ➜  dev-tutorial tree .
.
├── flow_modules
│   ├── aiflows
│   │   └── ChatFlowModule
│   │       ├── ...
│   │       ├── ChatAtomicFlow.py
│   │       ├── ChatAtomicFlow.yaml
│   │       ├── ...
│   │       ├── ...
│   │       └── __pycache__
│   │           ├── ChatAtomicFlow.cpython-39.pyc
│   │           └── __init__.cpython-39.pyc
│   └── nbaldwin
│       └── ChatInteractiveFlowModule
│           ├── ...
│           ├── ChatHumanFlowModule.py
│           ├── ChatHumanFlowModule.yaml
│           ├── README.md
│           ├── ...
│           └── __pycache__
│               ├── ChatHumanFlowModule.cpython-39.pyc
│               └── __init__.cpython-39.pyc
└── trivial_sync_demo.py

9 directories, 16 files
```
In this illustration, the `nbaldwin/ChatInteractiveFlowModule` flow module relies on the remote flow module `aiflows/ChatAtomicFlow`. Both dependencies are seamlessly synchronized under the flow_modules directory. The synchronization and importation of dependencies mirror each other, ensuring a consistent and logical approach across remote and local development environments.

____

**Next Tutorial**: [Typical Developer Workflows](./typical_developer_workflows.md)