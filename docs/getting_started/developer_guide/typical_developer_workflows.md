# Typical Developer Workflows
**prerequisites**: [Flow Module Management](./flow_module_management.md)

## Creating, Testing, and Publishing Your Own Flow Module

### By the Tutorial's End, I Will Have...

* Learned how to Create a Flow

* Learned how to Test a Flow

* Learned how to Publish a Flow

* Learned how to contributing to an existing flow


### Creating Your Own Flow Module

To start, create a local directory where you'll develop your flow module:

```shell
(aiflows) ➜  dev-tutorial mkdir PATH_TO_LOCAL_DEV_DIRECTORY/dev_UsefulChatBots
(aiflows) ➜  dev-tutorial cd PATH_TO_LOCAL_DEV_DIRECTORY/dev_UsefulChatBots
(aiflows) ➜  dev_UsefulChatBots touch __init__.py
(aiflows) ➜  dev_UsefulChatBots touch .gitignore
(aiflows) ➜  dev_UsefulChatBots touch EconomicExpertBot.py
(aiflows) ➜  dev_UsefulChatBots git init
(aiflows) ➜  dev_UsefulChatBots git:(main) ✗ git add .
(aiflows) ➜  dev_UsefulChatBots git:(main) ✗ git commit -m "initial commit"
[main (root-commit) e592fd1] initial commit
3 files changed, 0 insertions(+), 0 deletions(-)
create mode 100644 .gitignore
create mode 100644 EconomicExpertBot.py
create mode 100644 __init__.py
```

Next, we could either develop from scratch as in [Tutorial for AtomicFlow](../Tutorial/atomic_flow.md) or we could leverage an existing flow module and build upon it. In this tutorial, we'll develop our chatbot based on [aiflows/ChatFlowModule](https://huggingface.co/aiflows/ChatFlowModule) thanks to the modularity of Flows:

```python
dependencies = [
   {"url": "aiflows/ChatFlowModule", "revision": "main"},
]
from aiflows import flow_verse
flow_verse.sync_dependencies(dependencies)

from flow_modules.aiflows.ChatFlowModule import ChatAtomicFlow

class EconomicExpertBot(ChatAtomicFlow):
   def __init__(self, **kwargs):
	   super().__init__(**kwargs)
```

We recommend to associate your flow with a default yaml file as the default config. This default config will serve as a clear spec of the Flow class. For example, in our case:
```yaml
name: "EconomicExpertBot"
description: "A chatbot which answers questions about the economy."

input_interface:
 - "query"

output_interface:
 - "response"

system_message_prompt_template:
 _target_: aiflows.prompt_template.JinjaPrompt
 template: |2-
   You are an expertise in finance, economy and investment. When you explain something, you always provide associated statistical numbers, source of the information and concrete examples. You tend to explain things in a step-by-step fashion to help the reader to understand. You are also proficient in both English and Chinese. You can answer questions fluently in both languages.

 input_variables: []
```

This explicitly informs potential users about the `input_interface` and `output_interface`, which can be seen as the interface of our Flow. Since we're inheriting from `aiflows/ChatFlowModule.ChatAtomicFlow`, we also inherit the [default config](https://huggingface.co/aiflows/ChatFlowModule/blob/main/ChatAtomicFlow.yaml) from it. Therefore, our default config can be succinct and only needs to tweak some essential parameters.

Note that a flow module should ideally be a self-contained python module. Therefore, it's best to use relative import inside your code such that other users can use your flow instantly.

### Testing Your Own Flow Module

So far so good, we have created our own flow. Let's now try to test it:

```python
dependencies = [
    {"url": "yeeef/UsefulChatBots", "revision": "PATH_TO_LOCAL_DEV_DIRECTORY/dev_UsefulChatBots"},
]
from aiflows import flow_verse
flow_verse.sync_dependencies(dependencies)

import os

from flow_modules.yeeef.UsefulChatBots.EconomicExpertBot import EconomicExpertBot
from aiflows.flow_launchers import FlowLauncher


if __name__ == "__main__":
    # ~~~ Set the API information ~~~
    # OpenAI backend

    api_information = [ApiInfo(backend_used="openai", api_key=os.getenv("OPENAI_API_KEY"))]

    overrides = { "backend": {"api_infos": : api_information}}

    bot = EconomicExpertBot.instantiate_from_default_config(**overrides)
    # the data points in inputs must satisfy the requirements of input_keys
    data = [
        {
            "id": 0, "query": "What is CPI? What is the current CPI in the US?",
        },
    ]
    print(f"inputs: {data}")

    # init a minimal flow_launcher without specifying the output_keys, then
    # the full output_keys will be given
    outputs = FlowLauncher.launch(
        flow_with_interfaces={"flow": data},
        data=inputs,
    )
    print(outputs)
```

As we are developing locally, the remote revision does not exist yet, so we point the revision to the local path we just created: `PATH_TO_LOCAL_DEV_DIRECTORY/dev_UsefulChatBots`. Note that when we sync a local revision, instead of copying the files locally, we make a symbolic soft link. So you could just modify the code under `flow_modules` and the changes will be automatically propagated to the `PATH_TO_LOCAL_DEV_DIRECTORY/dev_UsefulChatBots`.

We also specify the namespace of our flow module: `yeeef/UsefulChatBots`. yeeef is my HuggingFace username, and you should replace it with your own Hugging Face username. Note that this `url` could be arbitrary as it does not exist online yet, but we highly recommend that the namespace of the flow module be consistent with your HuggingFace username, such that publishing it later will be seamless.

Then let’s execute the code and test our new flow:

```
(aiflows) ➜  dev-tutorial python ask_economic_expert_bot.py
inputs: [{'id': 0, 'query': 'What is CPI? What is the current CPI in the US?'}]
[2023-07-05 17:05:35,530][aiflows.base_flows.abstract][WARNING] - The raw response was not logged.
[{'id': 0, 'inference_outputs': [OutputMessage(message_id='d95683d6-9507-4a90-b290-6a43e609c904', created_at='2023-07-05 09:05:35.530972000', created_by='EconomicExpertBot', message_type='OutputMessage', data={'output_keys': ['response'], 'output_data': {'response': 'CPI, or the Consumer Price Index, is a measure that examines the weighted average of prices of a basket of consumer goods and services, such as transportation, food, and medical care. It is calculated by taking price changes for each item in the predetermined basket of goods and averaging them. Changes in the CPI are used to assess price changes associated with the cost of living.'}, 'missing_output_keys': []}, private_keys=['api_keys'])], 'error': None}]
```

Looks good! Now let’s publish it to the huggingface!

### Publishing Your Flow Module

Start by creating a new model on Hugging Face and it will be best to allign with the namespace when we are testing: `yeeef/UsefulChatBots`. Then press the botton `Create model`.
aligning it with the namespace used during testing: `yeeef/UsefulChatBots`. Click the `Create model` button to create the model.

![](https://hackmd.io/_uploads/r1iB4pGFn.png)

Then, you can either upload the files manually through the Hugging Face webpage or push your changes to the remote:

```shell
(aiflows) ➜  dev-tutorial cd PATH_TO_LOCAL_DEV_DIRECTORY/dev_UsefulChatBots
(aiflows) ➜  dev_UsefulChatBots git:(main) ✗ git remote add origin https://huggingface.co/yeeef/UsefulChatBots
(aiflows) ➜  dev_UsefulChatBots git:(main) ✗ git pull -r origin main
(aiflows) ➜  dev_UsefulChatBots git:(main) ✗ git push --set-upstream origin main
```

Congratulations! You now have your remote module online, available for everyone to use!


![](https://hackmd.io/_uploads/HJ4LNafF3.png)

## Contributing to an Existing Flow

In this tutorial, we continue to use the `trivial_sync_demo.py` (see [Flow Module Management](./flow_module_management.md)) script. As the dependencies are synced to your root directory, you can instantly modify the synced flow module according to your needs. Once you've made enough changes and feel ready to make a Pull Request (PR), you simply need to push your changes to the Hugging Face repository and create the PR.

For instance, let's say we want to update the dependency of [nbaldwin/ChatInteractiveFlowModule](https://huggingface.co/nbaldwin/ChatInteractiveFlowModule/tree/main) to the latest version of [aiflows/ChatAtomicFlow](https://huggingface.co/aiflows/ChatFlowModule):

```python
dependencies = [
    {"url": "aiflows/ChatFlowModule", "revision": "main"} # cae3fdf2f0ef7f28127cf4bc35ce985c5fc4d19a -> main
]
from aiflows import flow_verse
flow_verse.sync_dependencies(dependencies)

from flow_modules.aiflows.ChatFlowModule import ChatAtomicFlow

class ChatHumanFlowModule(ChatAtomicFlow):
    def __init__(self, **kwargs):
        
        ##SOME CODE
```

Firstly, navigate to the synced folder, initialize a git repository, and commit your changes:

```
(aiflows) ➜  dev-tutorial cd flow_modules/nbaldwin/ChatInteractiveFlowModule
(aiflows) ➜  ChatInteractiveFlowModule git init
Initialized empty Git repository in /Users/yeeef/Desktop/dlab-ra/dev-tutorial/flow_modules/nbaldwin/ChatInteractiveFlowModule/.git/
(aiflows) ➜  ChatInteractiveFlowModule git:(main) ✗ git add .
(aiflows) ➜  ChatInteractiveFlowModule git:(main) ✗ git commit -m "Change the dependency revision to main"
[main d7465df] Change the dependency revision to main
 1 file changed, 1 insertion(+), 1 deletion(-)
```

Next, you need to open a PR on the target Hugging Face repository. Navigate to `Community` and click on `New pull request`.

![](https://hackmd.io/_uploads/ry0f4pfF2.png)


Enter a brief description for your PR branch and click on `Create PR branch`.

![](https://hackmd.io/_uploads/S1aQV6fK3.png)


Once your PR branch has been created (for instance, `pr/2`), you'll need to push your changes to this branch:

```
(aiflows) ➜  ChatInteractiveFlowModule git:(main) git checkout -b pr/2
Switched to a new branch 'pr/2'
(aiflows) ➜  ChatInteractiveFlowModule git:(pr/2) git remote add origin https://huggingface.co/nbaldwin/ChatInteractiveFlowModule
(aiflows) ➜  ChatInteractiveFlowModule git:(pr/2) git pull -r origin pr/2
(aiflows) ➜  ChatInteractiveFlowModule git:(pr/2) git push origin pr/2:pr/2
Enumerating objects: 11, done.
Counting objects: 100% (11/11), done.
Delta compression using up to 10 threads
Compressing objects: 100% (8/8), done.
Writing objects: 100% (8/8), 952 bytes | 952.00 KiB/s, done.
Total 8 (delta 5), reused 0 (delta 0), pack-reused

 0
To https://huggingface.co/nbaldwin/ChatInteractiveFlowModule
   1849a87..1818057  pr/2 -> refs/pr/2
```

Finally, review your PR changes on the Hugging Face PR page and click the `Publish` button to finalize your submission.

![](https://hackmd.io/_uploads/rkvVV6MFn.png)

## Develop Over an Existing Flow and Publish it Under Your Namespace

As a Flow developer, you can easily develop based on any synced flow modules. However, instead of making a PR to the original repository, you may wish to publish it under your own namespace. This can be the case if you've made substantial changes that the original author might not prefer.

Let’s get back to our `trivial_sync_demo`, where we leverage `nbaldwin/ChatInteractiveFlowModule`. We have made some changes to it and want to publish it on our own as `yeeef/MyChatInteractiveFlowModule`. To do this, we recommend following steps:

**Step 1**: Manually copy the modified flow module out of the `flow_modules` directory:

```shell
(aiflows) ➜  dev-tutorial cp -r ./flow_modules/nbaldwin/ChatInteractiveFlowModules PATH_TO_LOCAL_DEV_DIRECTORY/MyChatInteractiveFlowModules
```

**Step 2**: Next, we can treat it as a local file directory and sync it with a local revision:

```python
dependencies = [
    {"url": "nbaldwin/ChatInteractiveFlowModules", "revision": "main"},
    {"url": "yeeef/MyChatInteractiveFlowModule", "revision": "PATH_TO_LOCAL_DEV_DIRECTORY/MyChatInteractiveFlowModules"},

]
from aiflows import flow_verse
flow_verse.sync_dependencies(dependencies)

from flow_modules.nbaldwin.ChatInteractiveFlowModules import ChatHumanFlowModule
from flow_modules.yeeef.MyChatInteractiveFlowModules import MyChatInteractiveFlowModules

if __name__ == "__main__":
	print("it is a trivial sync demo")
```

**Step 3**: Finally, follow the procedure outlined in [this](#creating-your-own-flow-module) section, and you are good to go!
