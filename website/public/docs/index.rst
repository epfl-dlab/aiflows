======================
Welcome to aiFlows! 🚀
======================

.. toctree::
   :titlesonly:
   :caption: Table of Contents
   :hidden:
   
   introduction/index
   installation/index
   getting_started/index
   contibution_info/index
   citation/index
   documentation/index


.. INTRODUCTION SECTION

.. include:: introduction/index.rst

.. INSTALLATION SECTION

.. include:: installation/index.rst


.. GETING STARTED SECTION

.. include:: getting_started/index.md
   :parser: myst_parser.sphinx_

.. figure:: ./media/previous_flows_rounded.png
   :align: center
   :alt: image
   :width: 1000px

   **The Flows framework exemplified.** The first column depicts examples of tools. Notably, 
   in the Flows framework, AI systems correspond to tools. The second column depicts Atomic Flows, effectively minimal wrappers around tools, 
   constructed from the example tools. The third column depicts examples of Composite Flows defining structured interaction between Atomic or Composite Flows. 
   The fourth column illustrates a specific Composite competitive coding Flow as those used in the experiments in the `paper`_ . 
   The fifth column outlines the structure of a hypothetical Flow, defining a meta-reasoning process that could support autonomous behavior.

.. _paper: https://arxiv.org/abs/2308.01285

.. CONTIBUTION SECTION SECTION

.. include:: contributing_info/index.rst

.. CITATION SECTION

.. include:: citation/index.md
   :parser: myst_parser.sphinx_


.. DOCUMENTATION SECTION
.. include:: documentation/index.rst