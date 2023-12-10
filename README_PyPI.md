<p align="center">
      <br/>
            <img src="https://github.com/epfl-dlab/aiflows/blob/main/assets/logo_text_statement_alt_rounded_corners.png?raw=true" alt="image" width="600" height="auto">
      <br/>
<p>

<p align="center">
    <a href="https://epfl-dlab.github.io/aiflows">
    <img alt="Website" src="https://img.shields.io/badge/website-online-green">
    </a>
    <a href="https://discord.gg/yFZkpD2HAh">
    <img alt="Static Badge" src="https://img.shields.io/badge/Discord-gray?style=flat&logo=discord&link=https%3A%2F%2Fdiscord.gg%2FNJuDxSafCY">
    </a>
    <a href="https://epfl-dlab.github.io/aiflows/docs/built_with_sphinx/html/index.html">
    <img alt="Documentation" src="https://img.shields.io/badge/docs-online-green">
    </a>
    <a href="https://www.python.org/downloads/release/python-3100/"><img alt="PyPi version" src="https://img.shields.io/badge/python-3.10-blue.svg"></a>
    <a href="https://arxiv.org/abs/2308.01285">
    <img alt="Documentation" src="https://img.shields.io/badge/arXiv-2308.01285-b31b1b.svg">
    </a>
</p>

🤖🌊 **aiFlows** embodies the <a href="assets/flows_paper.pdf">*Flows*</a> abstraction (<a href="https://arxiv.org/abs/2308.01285">arXiv</a>) and greatly simplifies the design and implementation of complex (work)Flows involving humans, AI systems, and tools. It enables:

- 🧩 Modularity: Flows can be stacked like LEGO blocks into arbitrarily nested structures with the complexity hidden behind a message-based interface
- 🤝 Reusability: Flows can be shared publicly on the FlowVerse, readily downloaded and reused as part of different Flows
- 🔀 Concurrency: Being consistent with the Actor model of concurrent computation, Flows are concurrency friendly – a necessary feature for a multi-agent future

## Flows in a Nutshell

The framework is centered around *Flows* and *messages*.
Flows represent the fundamental building block of computation. They are independent, self-contained, goal-driven entities able to complete a semantically meaningful unit of work.
To exchange information, Flows communicate via a standardized message-based interface. Messages can be of any type the recipient Flow can process.
<p align="center">
      <img src="https://github.com/epfl-dlab/aiflows/blob/main/assets/fig1_rounded_corners.png?raw=true" alt="image" width="1000" height="auto">
      <p align="justify">
      <strong>The <em>Flows</em> framework exemplified.</strong> The first column depicts examples of tools. Notably, in the Flows framework, AI systems correspond to tools. The second column depicts Atomic Flows, effectively minimal wrappers around tools constructed from the example tools. The third column depicts examples of Composite Flows defining structured interaction between _Atomic_ or _Composite_ Flows. The fourth column illustrates a specific _Composite_ competitive coding Flow as those used in the experiments in the paper. The fifth column outlines the structure of a hypothetical Flow, defining a meta-reasoning process that could support autonomous behavior.
      </p>
<p>

## FlowVerse in a Nutshell
The FlowVerse is a repository of Flows (powered by the 🤗 HuggingFace hub) created and shared by our community for everyone to use! With aiFlows, Flows can be readily downloaded, used, extended, or composed into novel, more complex Flows. For instance, sharing a Flow that uses only API-based tools (tools subsume models in the Flows abstraction) is as simple as sharing a config file (e.g., [here](https://huggingface.co/aiflows/AutoGPTFlowModule) is the AutoGPT Flow on FlowVerse). For the ones using ChatGPT, you could think of them as completely customizable open-source GPTs(++).

The FlowVerse is continuously growing. To explore the currently available Flows, check out the 🤲│flow-sharing Forum on the Discord [server](https://discord.gg/yFZkpD2HAh). Additionally, the _Tutorials_ and _Detailed Examples_ in the [Getting Started](https://epfl-dlab.github.io/aiflows/docs/built_with_sphinx/html/getting_started/index.html) sections cover some of the Flows we provide in more detail (e.g., the ChatAtomicFlow and QA, VisionAtomicFlow and VisualQA, ReAct and ReAct with human feedback, AutoGPT, etc.).

## Why should I use aiFlows?
AI is set to revolutionize the way we work. Our mission is to support AI researchers and to allow them to seamlessly share advancements with practitioners. This will establish a feedback loop, guiding progress toward beneficial directions while ensuring that everyone can freely access and benefit from the next-generation AI tools.

#### As a researcher, you will benefit from:
- The ability to design, implement, and study arbitrarily complex interactions
- Complete control and customizability (e.g., the tools, the specific Flows and the information they have access to, the choice of models and their deployment, etc.)
- The ability to readily reproduce, reuse, or build on top of Flows shared on the FlowVerse and systematically study them across different settings (the infrastructure in the <a href="https://github.com/epfl-dlab/cc_flows">cc_flows</a> repository could be a useful starting point in future studies)
- The ability to readily make your work accessible to practitioners and other researchers and access their feedback.

#### As a practitioner, you will benefit from the:
- The ability to design and implement arbitrarily complex interactions
- Complete control and customizability (e.g., the tools, the specific Flows and the information they have access to, the choice of models and their deployment, etc.)
- The ability to readily reuse or build on top of Flows shared on the FlowVerse
- Direct access to any advancements in the field.

To develop the next-generation AI tools and at the same time maximally benefit from them, developers and researchers need to have complete control over their workflows -- aiFlows strives to empower you to make each Flow your own! See the [contribute](#contribute) section for more information.

## Installation
The library requires Python 3.10+. To install the library, run the following command:

```shell
pip install aiflows
```

<details>
  <summary>Other installation options</summary>

### Install bleeding-edge version

```shell
git clone git@github.com:epfl-dlab/aiflows.git
cd aiflows
pip install -e .
```
</details>


## Getting Started

### [Quick start (🕓 5 min)](./website/public/docs/getting_started/Quick_Start/quick_start.md)

Here, you'll see how you can run inference with your first question-answering Flow, and you can trivially change between vastly different question-answering Flows thanks to the modular abstraction and FlowVerse!

### [Tutorial (🕓 20 min)](./website/public/docs/getting_started/Tutorial/tutorial_landing_page.md)

In this tutorial, we introduce you to the library's features through a walkthrough of how to build useful Flows of gradually increasing complexity. Starting from a vanilla QA Flow, we'll first extend it to a ReAct Flow, then ReAct with human feedback, and finish the tutorial with a version of AutoGPT!

### [Developer's Guide (🕓 10 min)](./website/public/docs/getting_started/developer_guide/developper_guide_landing_page.md)

We are constantly optimizing our Flow development workflow (pun intended:). In this short guide, we share our best tips so that you don't have to learn the hard way.

### [Detailed Examples](./website/public/docs/getting_started/detailed_examples/detailed_example_landing_page.md)

Many of the recently proposed prompting and collaboration strategies involving tools, humans, and AI models are, in essence, specific Flows (see the figure below). In the link above, you'll find a detailed walkthrough of how to build some representative workflows.

<p align="center">
      <img src="https://github.com/epfl-dlab/aiflows/raw/main/assets/previous_flows_rounded.png" alt="image" width="1000" height="auto">
      <p align="justify">
<p>

## Contribute

As mentioned above, our goal is to make Flows a community-driven project that will benefit researchers and developers alike (see the [Why should I use aiFlows?](#why-should-i-use-aiflows) section), and to achieve this goal, we need your help.

You can become a part of the project in a few ways:
- contribute to the aiFlows codebase: this will directly improve the library and benefit everyone using it
- contribute to the FlowVerse: by making your work accessible to everyone, others might improve your work and build on it, or you can build on others' work
- use the library in your creative projects, push it to its limits, and share your feedback: the proof of the pudding is in the eating, and the best way to identify promising directions, as well as important missing features, is by experimenting
- last but not least, ⭐ the repository and 📣 share aiFlows with your friends and colleagues; spread the word ❤️

We will support the community in the best way we can but also lead by example. In the coming weeks, we will share:
  - a roadmap for the library (FlowViz; FlowStudio; improve flexibility, developer experience, and support for concurrency, etc. -- feedback and help would be greatly appreciated!)
  - write-ups outlining features, ideas, and our long-term vision for Flows -- we encourage you to pick up any of these and start working on them in whatever way you see fit
  - a version of JARVIS -- your fully customizable open-source version of ChatGPT+(++), which we will continue building in public! We hope that this excites you as much as it excites us, and JARVIS will become one of those useful projects that will constantly push the boundaries of what's possible with Flows

We have tried to find a way for anyone to benefit by contributing to the project. The <a href="https://epfl-dlab.github.io/aiflows/docs/built_with_sphinx/html/contributing_info/contribute_index.html">Contribution Guide</a> describes our envisioned workflows in more detail (we would love to hear your feedback on this -- the Discord [server](https://discord.gg/yFZkpD2HAh) already has a channel for it :)).

In a nutshell, this is just the beginning, and we have a long way to go. Stay tuned, and let's work on a great (open-source) AI future together!

## Contributors

<a href="https://github.com/epfl-dlab/aiflows/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=epfl-dlab/aiflows" />
</a>

Made with [contrib.rocks](https://contrib.rocks).

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
