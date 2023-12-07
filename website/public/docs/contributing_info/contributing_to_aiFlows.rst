.. _contributing_to_ai_flows:

Contributing to aiFlows Library (for bug fixes and adding features)
======================================================================

**Step 1: Identifying and Reporting an Issue / Bug**
-------------------------------------------------------

**1.1. Check Existing Issues & Talk to the Community**
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Before creating a new issue, check if the problem you've encountered already exists. If it does, consider commenting on the existing issue to 
provide additional details or express your interest in working on it.

Community Discussion on Discord:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Additionally, for more immediate interaction and collaboration, you can discuss the issue on the project's `Discord`_ channel. 
Join the 💻│developers or 🐛│debugging channels to connect with the community, seek advice, and coordinate efforts. Engaging with the 
community on Discord can provide valuable insights and assistance throughout the issue resolution process.

**1.2. Creating a New Issue**
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If the issue doesn't exist, create a new one. Include a clear and concise title, detailed description of the problem, and steps to reproduce it. 
Utilize the "Report a Bug" template for bug reports and the "Feature Request" template for suggesting new features.

**Step 2: Getting Started with a Pull Request (PR)**
----------------------------------------------------------

**2.0. Inform the Community**
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Comment on the issue you're working on, informing others that you're actively working on a solution. 
Provide progress updates if needed. Also, inform the community on our `Discord`_ 🔨│community-projects forum that you're working on it. 
Engage with the community, share your ideas, and seek feedback on your pull request. This open communication is crucial not only for 
collaboration but also to inform others that you're actively working on the issue. This helps prevent duplicate work and ensures that community members are aware of ongoing efforts, 
fostering a collaborative and efficient development environment.

**2.1. Fork the Repository**
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

On the "aiflows" GitHub page, click "Fork" to create a copy of the repository under your GitHub account.

**2.2. Clone Your Fork**
^^^^^^^^^^^^^^^^^^^^^^^^^

Clone the forked repository to your local machine using the following command::

   git clone https://github.com/your-username/aiflows.git

**2.3. Create a New Branch**
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Create a new branch for your fix or feature::

   git checkout -b fix-branch

**Step 3: Coding and Making a Pull Request**
--------------------------------------------

**3.1 Make Changes & And adhere to aiFlow's coding practices**
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Implement your fix or feature. Follow best practices, and consider the project's :ref:`coding_standards`.

**3.2. Commit Changes**
^^^^^^^^^^^^^^^^^^^^^^^

Commit your changes with clear and descriptive messages::

   git add .
   git commit -m "Fix: Describe the issue or feature"

**3.3. Push Changes**
^^^^^^^^^^^^^^^^^^^^^^

Push your changes to your forked repository::

   git push origin fix-branch

**3.4. Create a Pull Request**
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

On the GitHub page of your fork, create a new pull request. Ensure you select the appropriate branch in the "base" and "compare" dropdowns. 
Make sure to check out this Github tutorial for more details: `Creating a pull request from a fork`_.

**3.5. Link the pull request to an issue**
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In the description or comments of your pull request, reference the issue it addresses. Use the keyword "fixes" followed by the issue number (e.g., "fixes #123"). 
This helps in automatically closing the related issue when the pull request is merged. 
Check out this Github tutorial for more details: `Linking a pull request to an issue`_.

**Step 4: Addressing Reviewer Concerns**
-----------------------------------------

**4.1. Reviewer Feedback**
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Reviewers may suggest changes to your code. Be open to feedback and make necessary adjustments.

**4.2. Coding Style**
^^^^^^^^^^^^^^^^^^^^^^

Ensure your code aligns with the project's coding style. If unsure, refer to the project's documentation or ask for clarification.

---------------

Thank you for considering contributing to the aiFlows library! Your dedication and effort are immensely appreciated. 
Contributors like you make a significant impact, and we want to express our gratitude. 
Remember, your name will proudly appear on our contributors' wall, showcasing your valuable contributions to the aiFlows project 🚀🔥

.. _Creating a pull request from a fork: https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/creating-a-pull-request-from-a-fork
.. _Linking a pull request to an issue: https://docs.github.com/en/issues/tracking-your-work-with-issues/linking-a-pull-request-to-an-issue
.. _Discord: https://discord.gg/yFZkpD2HAh