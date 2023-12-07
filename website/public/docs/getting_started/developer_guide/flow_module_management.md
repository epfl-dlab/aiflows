# Flow Module Management

The FlowVerse is a repository of Flows (powered by the 🤗 HuggingFace hub) created and shared by our community for everyone to use! With aiFlows, these Flows can be readily downloaded, used, extended or composed into novel, more complex Flows. For the ones using ChatGPT, you could think of them as open-source GPTs(++). 

In the heart of this platform, the community shares their unique Flows, encapsulated in what we call **flow modules**.

## Flow Modules

- Each Hugging Face published repository corresponds to a self-contained flow module. For instance, [aiflows/ChatInteractiveFlowModule](https://huggingface.co/aiflows/ChatInteractiveFlowModule) is a flow module.
- A module may include multiple Flow classes and potentially a default configuration YAML file. In the [aiflows/ChatInteractiveFlowModule](https://huggingface.co/aiflows/ChatInteractiveFlowModule) module, you can find [ChatHumanFlowModule.py](https://huggingface.co/aiflows/ChatInteractiveFlowModule/blob/main/ChatHumanFlowModule.py).
- Each Flow class can depend on other remote, publicly available modules. For example, [ChatHumanFlowModule.py](https://huggingface.co/aiflows/ChatInteractiveFlowModule/blob/main/ChatHumanFlowModule.py) depends on [aiflows/ChatFlowModule](https://huggingface.co/aiflows/ChatFlowModule).

## Syncing Flow Modules

To use or import a flow module, first sync it to the `flow_modules` directory in your root directory. You can then import it like any local Python package. Consider the following `trivial_sync_demo.py`, which relies on [saibo/ChatFlows](https://huggingface.co/saibo/ChatFlows):

```python
dependencies = [
    {"url": "saibo/ChatFlows", "revision": "main"},
]
from flows import flow_verse
flow_verse.sync_dependencies(dependencies)

from flow_modules.saibo.ChatFlows import ChatGPT4

if __name__ == "__main__":
	print("This is a trivial sync demo.")
```

This sync process, while initially unusual, offers several benefits:
- Inspect the implementation of remote flow modules without swapping between your IDE and a webpage. Additionally, benefit from IDE features like intellisense.
- Easily build on an existing implementation without needing to download or clone the repository yourself. You can then [create a PR with ease](TODO).

## Flow Module Namespace

- Remote flow modules are identified by their Hugging Face repo ID and revision, e.g., `saibo/ChatFlows:main`.
- Each locally synced flow module is a valid Python package found under the `flow_modules` directory. **Only one revision** is kept for each remote flow module, e.g., `flow_modules.saibo.ChatFlows`. If there's a revision conflict, a warning will prompt you to choose which version to keep.

For example, your file structure might look like this:

```shell
(flows) ➜  dev-tutorial tree .
.
├── flow_modules
│   ├── martinjosifoski
│   │   └── ChatAtomicFlow
│   │       ├── FLOW_MODULE_ID
│   │       ├── ChatAtomicFlow.py
│   │       ├── ChatAtomicFlow.yaml
│   │       ├── README.md
│   │       ├── __init__.py
│   │       └── __pycache__
│   │           ├── ChatAtomicFlow.cpython-39.pyc
│   │           └── __init__.cpython-39.pyc
│   └── saibo
│       └── ChatFlows
│           ├── FLOW_MODULE_ID
│           ├── ChatGPT4.py
│           ├── ChatGPT4.yaml
│           ├── README.md
│           ├── __init__.py
│           └── __pycache__
│               ├── ChatGPT4.cpython-39.pyc
│               └── __init__.cpython-39.pyc
└── trivial_sync_demo.py

9 directories, 16 files
```

As illustrated, the flow module `saibo/ChatFlows` depends on the remote flow module `martinjosifoski/ChatAtomicFlow`. Both of these dependencies are synchronized under the `flow_modules` directory. For the `saibo/ChatFlows` module, it syncs and imports its dependencies in the same way, maintaining consistency in the sync logic across both remote and local development.

```python
dependencies = [
    {"url": "martinjosifoski/ChatAtomicFlow", "revision": "cae3fdf2f0ef7f28127cf4bc35ce985c5fc4d19a"}
]
from flows import flow_verse
flow_verse.sync_dependencies(dependencies)

from flow_modules.martinjosifoski.ChatAtomicFlow import ChatAtomicFlow

class ChatGPT4(ChatAtomicFlow):
    def __init__(self, **kwargs):
```
The namespace for flow modules is consistent with its Hugging Face repo ID, meaning `martinjosifoski/ChatAtomicFlow` will be synced as `flow_modules.martinjosifoski.ChatAtomicFlow`.

If you wish to discard all your changes to a synced module, you can add an `overwrite` parameter to the dependencies. This will cause all of your modifications to be replaced with the original content of the specified revision:

```python
dependencies = [
    {"url": "martinjosifoski/ChatAtomicFlow", "revision": "cae3fdf2f0ef7f28127cf4bc35ce985c5fc4d19a", "overwrite": True}
]
```

Note that HuggingFace's user name and repository name can be prefixed with numbers. For example `1234/6789` is a valid repository id for HuggingFace. However, python does not allow its module name to be prefixed with numbers. `import 1234.6789` is illegal. In Flows, the repository id of the flow module has following implications:

- the user name can be prefixed with a number, as we cannot ask a user to change their name. The flow module will be synced into `./flow_modules/user_{NUMBER_PREFIX_USERNAME}`. So we add a prefix to the synced python module, such that it can be correctly imported.
- the repository name **cannot** be prefixed with a number. Repository name is easy to change. A alphabetic-prefixed name is also easier for your audience to understand.
