=========================
Getting started tutorial
=========================

Welcome to the tutorial section of the Flows library! These tutorials will guide you through the essential features and functionalities of the library, teaching you to efficiently use existing flows, and craft new complex flows for your projects.

-----------------------------
Existing Flows
-----------------------------

To begin, we will explore how you can use existing flows, already uploaded by others in the FlowVerse, the repository of flows hosted on HuggingFaceHub.

- :ref:`load_flowverse`.
- :ref:`flow_launcher`.
- :ref:`visualization_toolkit` to inspect the execution of a flow.

-----------------------------
Crafting New Flows
-----------------------------
The library really shines when you use existing flows as building blocks towards crafting flows specific to your task. Next, we will:

- :ref:`write_atomic`, adding more basic building blocks to your toolkit.
- :ref:`write_composite`, to craft ever more complex flows to fit your needs.
- :ref:`caching`, to save time and money by not executing flows that were already executed before
- :ref:`history`, to know what is logged and control what will appear in the visualization toolkit.
- :ref:`share_flow`, making your flows available for others to build upon

-----------------------------
Putting It All Together: Complex Flows
-----------------------------

Finally, we will put everything together and guide you through building complex flows. In this section, we will provide practical examples that demonstrate the capabilities of our library:

- Daily arxiv summarizer and QA: an example flow that allows the user to receive a summary of what happened on arXiv the day before and engage in QA with an AI agent about the papers.

- Self-Refine FlowReAct: A spin around the standard ReAct flow, making it exploit the compositionality of flows.

- Competitive Coding Flows (link to github): flows that tackle competitive coding problems that we study in the paper(link to paper)

By the end of these tutorials, you will have a solid understanding of flows and be equipped to harness their power, create custom flows, and tackle complex tasks with ease. So, let's dive in!

.. toctree::
    :titlesonly:
    :glob:

    A1_load_flowverse
    A2_flowlauncher
    A3_visualization
    B1_write_atomic
    B2_write_composite
    B3_caching
    B4_history
    B5_share_flow