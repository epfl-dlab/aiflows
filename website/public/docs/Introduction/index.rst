Flows in a Nutshell
-------------------
The framework is centered around *Flows* and *messages*.
Flows represent the fundamental building block of computation. They are independent, self-contained, 
goal-driven entities able to complete a semantically meaningful unit of work.
To exchange information, Flows communicate via a standardized message-based interface. 
Messages can be of any type the recipient Flow can process.

.. raw:: html
      <p align="center">
            <img src="./media/fig1_rounded_corners.png" alt="image" width="1000" height="auto">
            <p align="justify">
            <strong>The <em>Flows</em> framework exmplified.</strong> The first column depicts examples of tools. Notably, in the Flows framework, 
            AI systems correspond to tools. The second column depicts Atomic Flows, effectively minimal wrappers around tools, constructed from the 
            example tools. The third column depicts examples of Composite Flows defining structured interaction between Atomic or Composite Flows. 
            The fourth column illustrates a specific Composite competitive coding Flow as those used in the 
            experiments in the <a href="https://arxiv.org/abs/2308.01285">paper</a>. The fifth column outlines the structure 
            of a hypothetical Flow, defining a meta-reasoning process that could support autonomous behavior.
            </p>
      <p>

FlowVerse in a Nutshell
-----------------------

The FlowVerse is a repository of Flows (powered by the 🤗 HuggingFace hub) created and shared by our community for everyone to use! 
With aiFlows, these Flows can be readily downloaded, used, extended or composed into novel, more complex Flows. 
For the ones using ChatGPT, you could think of them as open-source GPTs(++).

Why should I use aiFlows ?
--------------------------

AI is set to revolutionize the way we work. Our mission is to support AI researchers and to allow them to seamlessly share advancements with practitioners. 
This will establish a feedback loop, guiding progress toward beneficial directions while ensuring that everyone can freely access and benefit from the next-generation AI tools.