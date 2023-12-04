<p align="center">
      <br/>
            <img src="assets/logo_text_statement_alt_rounded_corners.png" alt="image" width="600" height="auto">
      <br/>
<p>

<p align="center">
    <a href="https://epfl-dlab.github.io/flows">
    <img alt="Website" src="https://img.shields.io/badge/website-online-green">
    </a>
    <a href="https://discord.gg/NJuDxSafCY">
    <img alt="Static Badge" src="https://img.shields.io/badge/Discord-gray?style=flat&logo=discord&link=https%3A%2F%2Fdiscord.gg%2FNJuDxSafCY">
    </a>
    <a href="https://epfl-dlab.github.io/flows/docs/built_with_sphinx/html/index.html">
    <img alt="Documentation" src="https://img.shields.io/badge/docs-online-green">
    </a>
    <a href="https://www.python.org/downloads/release/python-3100/"><img alt="PyPi version" src="https://img.shields.io/badge/python-3.10-blue.svg"></a>
    <a href="https://arxiv.org/abs/2308.01285">
    <img alt="Documentation" src="https://img.shields.io/badge/arXiv-2308.01285-b31b1b.svg">
    </a>
</p>

🤖🌊 **aiFlows** embodies the <a href="https://arxiv.org/abs/2308.01285">*Flows*</a> abstraction and greatly simplifies the design and implementation of complex (work)Flows involving humans, AI systems, and tools. It enables:

- 🧩 Modularity: Flows can be stacked like lego-blocks into arbitrarily nested structures with the complexity hidden behind a message-based interface
- 🤝 Reusability: Flows can be shared publicly on the FlowVerse, readily downloaded and reused as part of different Flows
- 🔀 Concurrency: Being consistent with the Actor model of concurrent computation, Flows are concurrency friendly – a necessary feature for a multi-agent future

## Flows in a Nutshell

The framework is centered around *Flows* and *messages*.
Flows represent the fundamental building block of computation. They are independent, self-contained, goal-driven entities able to complete a semantically meaningful unit of work.
To exchange information, Flows communicate via a standardized message-based interface. Messages can be of any type the recipient Flow can process.
<p align="center">
      <img src="assets/fig1_rounded_corners.png" alt="image" width="1000" height="auto">
      <p align="justify">
      <strong>The <em>Flows</em> framework exmplified.</strong> The first column depicts examples of tools. Notably, in the Flows framework, AI systems correspond to tools. The second column depicts Atomic Flows, effectively minimal wrappers around tools, constructed from the example tools. The third column depicts examples of Composite Flows defining structured interaction between Atomic or Composite Flows. The fourth column illustrates a specific Composite competitive coding Flow as those used in the experiments in the <a href="https://arxiv.org/abs/2308.01285">paper</a>. The fifth column outlines the structure of a hypothetical Flow, defining a meta-reasoning process that could support autonomous behavior.
      </p>
<p>

## Why should I use aiFlows?
AI is set to revolutionarize the way we work. Our mission is to support AI researchers, and to allow them to seemlessly share advancements with practitioners. This will establish a feedback loop, guiding progress towards beneficial directions while ensuring that everyone can freely acess and benefit from the next-generation AI tools.

<u>As a researcher you will benefit from the:</u>
- ability to design, implement, and study arbitrarily complex interactions
- complete control and customizability (e.g., the tools, the specific Flows and the information they have access to, the choice of models and their deployment, etc.)
- ability to readily reproduce, reuse, or build on top of Flows shared on the FlowVerse, and systematically study them across different settings (the infrastrcture in the <a href="https://github.com/epfl-dlab/cc_flows">cc_flows</a> repository could be a useful starting point in future studies)
- ability to readily make your work accessible with practitioners and other researchers, and access their feedback.

<u>As a practitioner you will benefit from the:</u>
- ability to design and implement arbitrarily complex interactions
- complete control and customizability (e.g., the tools, the specific Flows and the information they have access to, the choice of models and their deployment, etc.)
- ability to readily reuse or build on top of Flows shared on the FlowVerse
- direct access to any advancements in the field.

To develop the next-generation of AI tools, and at the same time maximally benefit from it, developers and researchers need to have complete control over their workflows -- aiFlows strives to empower you to make each Flow your own!

Furthermore, we strongly believe that the proof of the pudding is in the eating, and the best way to identify promising directions as well as important missing features is by experimenting. Thefore, we invite researchers and developers alike to be creative and start devlopping Flows that will push the library to its breaking point. We encourage you to try to develop your idea in the public; you are likely to find others interested in your project, benefit from the hivemind and progress faster.
We will try to support you in any way possible, but also lead by example, and work towards JARVIS -- your fully customizable open-source version of ChatGPT+(++)! This is just the beginning, and we have a long way to go. Let's work on a great future, [together](##Contributing)!

(ToDo: Verify that the link above works)

## Installation
(ToDo: Do we need any other information?)

The library requires Python 3.10+. To install the library run the following command:

```shell
pip install aiflows
```

<details>
  <summary>Other installation options</summary>

### Install bleeding-edge (ToDo: is this the easiest way to do it?)

```shell
git clone git@github.com:epfl-dlab/aiflows.git
cd aiflows
pip install -e .
```
</details>


## Getting Started

### Hello World

```python
# run.py
import os

import hydra

import flows
from flows.flow_launchers import FlowLauncher
from flows.backends.api_info import ApiInfo
from flows.utils.general_helpers import read_yaml_file

# -----------------------------------
# Step 1: Syncronize the dependencies
# -----------------------------------
# Specifies the Flows in the FlowVerse that this code depends on

from flows import flow_verse

dependencies = [
    {"url": "aiflows/ChatFlowModule", "revision": "a749ad10ed39776ba6721c37d0dc22af49ca0f17"},
]
flow_verse.sync_dependencies(dependencies)

# -------------------------------
# Step 2: Set the API information
# -------------------------------
# Note that we support many backends including locally hosted models (shout-out to LiteLLM) and vision models
api_information = [ApiInfo(backend_used="openai", api_key=os.getenv("OPENAI_API_KEY"))]

# ----------------------------
# Step 3: Instantiate the Flow
# ----------------------------
# ToDo: Showcase that we can easily switch between simpleQA, ReAct or AutoGPT
# ToDo: Can this be simplified for the hello world?

root_dir = "."
cfg_path = os.path.join(root_dir, "simpleQA.yaml")
cfg = read_yaml_file(cfg_path)

cfg["flow"]["backend"]["api_infos"] = api_information

# ~~~ Instantiate the Flow ~~~
flow_with_interfaces = {
      "flow": hydra.utils.instantiate(cfg["flow"], _recursive_=False, _convert_="partial"),
      "input_interface": (
      None
      if cfg.get("input_interface", None) is None
      else hydra.utils.instantiate(cfg["input_interface"], _recursive_=False)
      ),
      "output_interface": (
      None
      if cfg.get("output_interface", None) is None
      else hydra.utils.instantiate(cfg["output_interface"], _recursive_=False)
      ),
}

# -------------------
# Step 4: Define data
# -------------------
data = {"id": 0, "question": "Who was the NBA champion in 2023?"}  # This can be a list of samples

# ---------------------
# Step 5: Run inference
# ---------------------
_, outputs = FlowLauncher.launch(
      flow_with_interfaces=flow_with_interfaces, data=data, path_to_output_file=path_to_output_file
)

# ~~~ Print the output ~~~
flow_output_data = outputs[0]
print(flow_output_data)
```


Run the Flow on your terminal

```bash
python run.py
```

______________________________________________________________________

### Tutorials

To get a deeper understanding of the library go through the <a href="ToDoAddLink">hands on tutorials</a> that introduce you to the library's features by buidling useful Flows while gradually increasing complexity:

<a href="AddLink">VanillaQA-to-AutoGPT</a>
- Introduces the FlowVerse
- ... ToDO

<a href="AddLink">VanillaQA-to-AutoGPT</a>
- ...

### Examples

Additionally, we provide detailed walkthough of the Flows used in the tutorials, and more (e.g., visionQA, JARVIS (keeping a placeholder and saying coming soon sufficies)), <a href=ToDoAddLink>here</a>.

## Contributing
(ToDo: Nicky)

(ToDo: Include a link to the roadmap. How do we showcase it? Encourage people to pick-up items not in our list. Encourage people that have ambitious projects, consider building them on top of Flows, and would like support / coordination to reach out.  Encourage ppl that build infrastructural goals that are related, aligned, or can complement each other to reach out to us so that we coordinate.)

A non-comprehensive list of items include in the roadmap:
- JARVIS
- conditionals
- FlowViz
- Concurrency beyond data paralelism
- Further simplification of the developer experience (feedback required!)
- FlowsStudio

------
(old, I left in case you find it useful)

There are two ways to contribute to the project: by contributing to the **codebase** or by contributing to the **Flow-verse**.

- **Codebase**: We welcome contributions to the project and accept pull requests of all sorts: documentation, code, bug fixes, etc.
- **Flow-verse**: We hope to establish flows as a platform to enable collaboration, sharing, and reusing. Uploading your work to the Flow-verse is a great way to contribute to the community and to the project.

Last but not least, if you want to prepare educational material (tutorials, videos, etc.) about flows, we would love to hear from you! We are happy to link to your content from the project website.

All Github contributors will be explicitly named in release notes of future versions of the library. If anything is unclear, confusing, or needs to be refactored, please let us know by opening an issue on the repository.

## Citation

To reference the 🤖🌊 **aiFlows** library, please cite the paper [Flows: Building Blocks of Reasoning and Collaborating AI](https://arxiv.org/pdf/2308.01285.pdf):

```
@misc{josifoski2023flows,
      title={Flows: Building Blocks of Reasoning and Collaborating AI},
      author={Martin Josifoski and Lars Klein and Maxime Peyrard and Yifei Li and Saibo Geng and Julian Paul Schnitzler and Yuxing Yao and Jiheng Wei and Debjit Paul and Robert West},
      year={2023},
      eprint={2308.01285},
      archivePrefix={arXiv},
      primaryClass={cs.AI}
}
```

# ToDO

- Which version of the paper to link?
- Make sure that the library is published as aiflows on pip (check if `flows` is hardcoded somewhere in the context of the loggers)
- Check if `together` links to Contributing
- Can one install the library with conda?
- Should we have a dedicated list of the features?
