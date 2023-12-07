Flows in a Nutshell
---------------------

The framework is centered around *Flows* and *messages*.
Flows represent the fundamental building block of computation. They are independent, self-contained, 
goal-driven entities able to complete a semantically meaningful unit of work.
To exchange information, Flows communicate via a standardized message-based interface. 
Messages can be of any type the recipient Flow can process.

.. figure:: ./media/fig1_rounded_corners.png
   :align: center
   :alt: image
   :width: 1000px

   **The Flows framework exemplified.** The first column depicts examples of tools. Notably, in the Flows framework, AI systems correspond to tools. 
   The second column depicts Atomic Flows, effectively minimal wrappers around tools, constructed from the example tools. 
   The third column depicts examples of Composite Flows defining structured interaction between Atomic or Composite Flows. 
   The fourth column illustrates a specific Composite competitive coding Flow as those used in the experiments in the 
   `paper`_. 
   The fifth column outlines the structure of a hypothetical Flow, defining a meta-reasoning process that could support autonomous behavior.

.. _paper: https://arxiv.org/abs/2308.01285

FlowVerse in a Nutshell
----------------------------

The FlowVerse is a repository of Flows (powered by the 🤗 HuggingFace hub) created and shared by our community for everyone to use! 
With aiFlows, these Flows can be readily downloaded, used, extended or composed into novel, more complex Flows. 
For the ones using ChatGPT, you could think of them as open-source GPTs(++).

Why should I use aiFlows?
----------------------------

AI is poised to revolutionize the way we work. Our mission is to support AI researchers and enable them to seamlessly share advancements with practitioners. This establishes a feedback loop, guiding progress towards beneficial directions while ensuring that everyone can freely access and benefit from the next-generation AI tools.

As a researcher, you will benefit from:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- The ability to design, implement, and study arbitrarily complex interactions.
- Complete control and customizability (e.g., the tools, the specific Flows and the information they have access to, the choice of models and their deployment, etc.).
- The ability to readily reproduce, reuse, or build on top of Flows shared on the FlowVerse and systematically study them across different settings (the infrastructure in the `cc_flows` repository could be a useful starting point in future studies).
- The ability to readily make your work accessible to practitioners and other researchers and access their feedback.

As a practitioner, you will benefit from:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- The ability to design and implement arbitrarily complex interactions.
- Complete control and customizability (e.g., the tools, the specific Flows and the information they have access to, the choice of models and their deployment, etc.).
- The ability to readily reuse or build on top of Flows shared on the FlowVerse.
- Direct access to any advancements in the field.

To develop the next-generation AI tools and simultaneously maximize the benefits, developers and researchers need to have complete control over their workflows. aiFlows strives to empower you to make each Flow your own! See the `contribute` section for more information.

