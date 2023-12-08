## Getting Started

### [Quick start (🕓 5 min)](./Quick_Start/quick_start.md)

Here, you'll see how you can run inference with your first question-answering Flow, and you can trivially change between vastly different question-answering Flows thanks to the modular abstraction and FlowVerse!

### [Tutorial (🕓 20 min)](./Tutorial/tutorial_landing_page.md)

In this tutorial, we introduce you to the library's features through a walkthrough of how to build useful Flows of gradually increasing complexity. Starting from a vanilla QA Flow, we'll first extend it to a ReAct Flow, then ReAct with human feedback, and finish the tutorial with a version of AutoGPT!

### [Developer's Guide (🕓 10 min)](./developer_guide/developper_guide_landing_page.md)

We are constantly optimizing our Flow development workflow (pun intended:). In this short guide, we share our best tips so that you don't have to learn the hard way.

### [Detailed Examples](./detailed_examples/detailed_example_landing_page.md)
Many of the recently proposed prompting and collaboration strategies involving tools, humans, and AI models are, in essence, specific Flows (see the figure below). In the link above, you'll find a detailed walkthrough of how to build some representative workflows.



![The Flows framework exemplified.](/media/previous_flows_rounded.png)
**The Flows framework exemplified.** The first column depicts examples of tools. Notably, in the Flows framework, AI systems correspond to tools. The second column depicts Atomic Flows, effectively minimal wrappers around tools, constructed from the example tools. The third column depicts examples of Composite Flows defining structured interaction between Atomic or Composite Flows. The fourth column illustrates a specific Composite competitive coding Flow as those used in the experiments in the [paper](https://arxiv.org/abs/2308.01285). The fifth column outlines the structure of a hypothetical Flow, defining a meta-reasoning process that could support autonomous behavior.


