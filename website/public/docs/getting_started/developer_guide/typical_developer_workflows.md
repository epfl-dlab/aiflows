# Typical Developer Workflows


## Creating, Testing, and Publishing Your Own Flow Module

In this tutorial, we will guide you on *Creating, Testing, and Publishing* your own flow module.

### Creating Your Own Flow Module

To start, create a local directory where you'll develop your flow module:

```shell
(flows) ➜  dev-tutorial mkdir PATH_TO_LOCAL_DEV_DIRECTORY/dev_UsefulChatBots
(flows) ➜  dev-tutorial cd PATH_TO_LOCAL_DEV_DIRECTORY/dev_UsefulChatBots
(flows) ➜  dev_UsefulChatBots touch __init__.py
(flows) ➜  dev_UsefulChatBots touch .gitignore
(flows) ➜  dev_UsefulChatBots touch EconomicExpertBot.py
(flows) ➜  dev_UsefulChatBots git init
(flows) ➜  dev_UsefulChatBots git:(main) ✗ git add .
(flows) ➜  dev_UsefulChatBots git:(main) ✗ git commit -m "initial commit"
[main (root-commit) e592fd1] initial commit
3 files changed, 0 insertions(+), 0 deletions(-)
create mode 100644 .gitignore
create mode 100644 EconomicExpertBot.py
create mode 100644 __init__.py
```

Next, we could either develop from scratch as in [Tutorial for AtomicFlow](https://hackmd.io/9NxZV0xhRN-UEdjZ8Vu9Lw) or we could leverage an existing flow module and build upon it. In this tutorial, we'll develop our chatbot based on [saibo/ChatFlows](https://huggingface.co/saibo/ChatFlows) thanks to the modularity of Flows:

```python
dependencies = [
   {"url": "saibo/ChatFlows", "revision": "main"},
]
from flows import flow_verse
flow_verse.sync_dependencies(dependencies)

from flow_modules.saibo.ChatFlows import ChatGPT4

class EconomicExpertBot(ChatGPT4):
   def __init__(self, **kwargs):
	   super().__init__(**kwargs)
```

We recommend to associate your flow with a default yaml file as the default config. This default config will serve as a clear spec of the Flow class. For example, in our case:
```yaml
name: "EconomicExpertBot"
verbose: False
description: "A chatbot which answers questions about the economy."

input_interface:
 - "query"

output_interface:
 - "response"

system_message_prompt_template:
 _target_: langchain.PromptTemplate
 template: |2-
   You are an expertise in finance, economy and investment. When you explain something, you always provide associated statistical numbers, source of the information and concrete examples. You tend to explain things in a step-by-step fashion to help the reader to understand. You are also proficient in both English and Chinese. You can answer questions fluently in both languages.

 input_variables: []
 template_format: jinja2
```

This explicitly informs potential users about the `input_interface` and `output_interface`, which can be seen as the interface of our Flow. Since we're inheriting from `saibo/ChatFlows.ChatGPT4`, we also inherit the [default config](https://huggingface.co/saibo/ChatFlows/blob/main/ChatGPT4.yaml) from it. Therefore, our default config can be succinct and only needs to tweak some essential parameters.

Note that a flow module should ideally be a self-contained python module. Therefore, it's best to use relative import inside your code such that other users can use your flow instantly.

### Testing Your Own Flow Module

So far so good, we have created our own flow. Let's now try to test it:

```python
dependencies = [
    {"url": "yeeef/UsefulChatBots", "revision": "PATH_TO_LOCAL_DEV_DIRECTORY/dev_UsefulChatBots"},
]
from flows import flow_verse
flow_verse.sync_dependencies(dependencies)

import os

from flow_modules.yeeef.UsefulChatBots.EconomicExpertBot import EconomicExpertBot
from flows.flow_launchers import FlowLauncher


if __name__ == "__main__":
    openai_key = os.environ.get("OPENAI_API_KEY")
    bot = EconomicExpertBot.instantiate_from_default_config(overrides={"verbose": False, "api_key": openai_key})
    # the data points in inputs must satisfy the requirements of input_keys
    inputs = [
        {
            "id": 0, "query": "What is CPI? What is the current CPI in the US?",
        },
    ]
    print(f"inputs: {inputs}")

    # init a minimal flow_launcher without specifying the output_keys, then
    # the full output_keys will be given
    outputs = FlowLauncher.launch(
        flow_with_interfaces={"flow": bot},
        data=inputs,
        api_keys={"openai": os.getenv("OPENAI_API_KEY")},
    )
    print(outputs)
```

As we are developing locally, the remote revision does not exist yet, so we point the revision to the local path we just created: `PATH_TO_LOCAL_DEV_DIRECTORY/dev_UsefulChatBots`. Note that when we sync a local revision, instead of copying the files locally, we make a symbolic soft link. So you could just modify the code under `flow_modules` and the changes will be automatically propagated to the `PATH_TO_LOCAL_DEV_DIRECTORY/dev_UsefulChatBots`.

We also specify the namespace of our flow module: `yeeef/UsefulChatBots`. yeeef is my HuggingFace username, and you should replace it with your own Hugging Face username. Note that this `url` could be arbitrary as it does not exist online yet, but we highly recommend that the namespace of the flow module be consistent with your HuggingFace username, such that publishing it later will be seamless.

Then let’s execute the code and test our new flow:

```
(flows) ➜  dev-tutorial python ask_economic_expert_bot.py
inputs: [{'id': 0, 'query': 'What is CPI? What is the current CPI in the US?'}]
[2023-07-05 17:05:35,530][flows.base_flows.abstract][WARNING] - The raw response was not logged.
[{'id': 0, 'inference_outputs': [OutputMessage(message_id='d95683d6-9507-4a90-b290-6a43e609c904', created_at='2023-07-05 09:05:35.530972000', created_by='EconomicExpertBot', message_type='OutputMessage', data={'output_keys': ['response'], 'output_data': {'response': 'CPI, or the Consumer Price Index, is a measure that examines the weighted average of prices of a basket of consumer goods and services, such as transportation, food, and medical care. It is calculated by taking price changes for each item in the predetermined basket of goods and averaging them. Changes in the CPI are used to assess price changes associated with the cost of living.'}, 'missing_output_keys': []}, private_keys=['api_keys'])], 'error': None}]
```

Looks good! Now let’s publish it to the huggingface!

### Publishing Your Flow Module

Start by creating a new model on Hugging Face and it will be best to allign with the namespace when we are testing: `yeeef/UsefulChatBots`. Then press the botton `Create model`.
aligning it with the namespace used during testing: `yeeef/UsefulChatBots`. Click the `Create model` button to create the model.

![](https://hackmd.io/_uploads/r1iB4pGFn.png)

Then, you can either upload the files manually through the Hugging Face webpage or push your changes to the remote:

```shell
(flows) ➜  dev-tutorial cd PATH_TO_LOCAL_DEV_DIRECTORY/dev_UsefulChatBots
(flows) ➜  dev_UsefulChatBots git:(main) ✗ git remote add origin https://huggingface.co/yeeef/UsefulChatBots
(flows) ➜  dev_UsefulChatBots git:(main) ✗ git pull -r origin main
(flows) ➜  dev_UsefulChatBots git:(main) ✗ git push --set-upstream origin main
```

Congratulations! You now have your remote module online, available for everyone to use!


![](https://hackmd.io/_uploads/HJ4LNafF3.png)

## Contributing to an Existing Flow

In this tutorial, we continue to use the `trivial_sync_demo.py` script. As the dependencies are synced to your root directory, you can instantly modify the synced flow module according to your needs. Once you've made enough changes and feel ready to make a Pull Request (PR), you simply need to push your changes to the Hugging Face repository and create the PR.

For instance, let's say we want to update the dependency of [saibo/ChatFlows](https://huggingface.co/saibo/ChatFlows) to the latest version of [martinjosifoski/ChatAtomicFlow](https://huggingface.co/martinjosifoski/ChatAtomicFlow/tree/main):

```python
dependencies = [
    {"url": "martinjosifoski/ChatAtomicFlow", "revision": "main"} # cae3fdf2f0ef7f28127cf4bc35ce985c5fc4d19a -> main
]
from flows import flow_verse
flow_verse.sync_dependencies(dependencies)

from flow_modules.martinjosifoski.ChatAtomicFlow import ChatAtomicFlow

class ChatGPT4(ChatAtomicFlow):
    def __init__(self, **kwargs):
```

Firstly, navigate to the synced folder, initialize a git repository, and commit your changes:

```
(flows) ➜  dev-tutorial cd flow_modules/saibo/ChatFlows
(flows) ➜  ChatFlows git init
Initialized empty Git repository in /Users/yeeef/Desktop/dlab-ra/dev-tutorial/flow_modules/saibo/ChatFlows/.git/
(flows) ➜  ChatFlows git:(main) ✗ git add .
(flows) ➜  ChatFlows git:(main) ✗ git commit -m "Change the dependency revision to main"
[main d7465df] Change the dependency revision to main
 1 file changed, 1 insertion(+), 1 deletion(-)
```

Next, you need to open a PR on the target Hugging Face repository. Navigate to `Community` and click on `New pull request`.

![](https://hackmd.io/_uploads/ry0f4pfF2.png)


Enter a brief description for your PR branch and click on `Create PR branch`.

![](https://hackmd.io/_uploads/S1aQV6fK3.png)


Once your PR branch has been created (for instance, `pr/2`), you'll need to push your changes to this branch:

```
(flows) ➜  ChatFlows git:(main) git checkout -b pr/2
Switched to a new branch 'pr/2'
(flows) ➜  ChatFlows git:(pr/2) git remote add origin https://huggingface.co/saibo/ChatFlows
(flows) ➜  ChatFlows git:(pr/2) git pull -r origin pr/2
(flows) ➜  ChatFlows git:(pr/2) git push origin pr/2:pr/2
Enumerating objects: 11, done.
Counting objects: 100% (11/11), done.
Delta compression using up to 10 threads
Compressing objects: 100% (8/8), done.
Writing objects: 100% (8/8), 952 bytes | 952.00 KiB/s, done.
Total 8 (delta 5), reused 0 (delta 0), pack-reused

 0
To https://huggingface.co/saibo/ChatFlows
   1849a87..1818057  pr/2 -> refs/pr/2
```

Finally, review your PR changes on the Hugging Face PR page and click the `Publish` button to finalize your submission.

![](https://hackmd.io/_uploads/rkvVV6MFn.png)

## Develop Over an Existing Flow and Publish it Under Your Namespace

As a Flow developer, you can easily develop based on any synced flow modules. However, instead of making a PR to the original repository, you may wish to publish it under your own namespace. This can be the case if you've made substantial changes that the original author might not prefer.

Let’s get back to our `trivial_sync_demo`, where we leverage `saibo/ChatFlows`. We have made some changes to it and want to publish it on our own as `yeeef/MyChatFlows`. To do this, we recommend following steps:

**Step 1**: Manually copy the modified flow module out of the `flow_modules` directory:

```shell
(flows) ➜  dev-tutorial cp -r ./flow_modules/saibo/ChatFlows PATH_TO_LOCAL_DEV_DIRECTORY/MyChatFlows
```

**Step 2**: Next, we can treat it as a local file directory and sync it with a local revision:

```python
dependencies = [
    {"url": "saibo/ChatFlows", "revision": "main"},
    {"url": "yeeef/MyChatFlows", "revision": "PATH_TO_LOCAL_DEV_DIRECTORY/MyChatFlows"},

]
from flows import flow_verse
flow_verse.sync_dependencies(dependencies)

from flow_modules.saibo.ChatFlows import ChatGPT4
from flow_modules.yeeef.MyChatFlows import MyChatGPT4

if __name__ == "__main__":
	print("it is a trivial sync demo")
```

**Step 3**: Finally, follow the procedure outlined in [this](###Creating,-Testing,-and-Publishing-Your-Own-Flow-Module) section, and you are good to go!
