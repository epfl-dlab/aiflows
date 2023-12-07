.. _automating_doc:

===========================================================
Automating the documentation of a Flow on  the FlowVerse
===========================================================

Documenting your Flow is a crucial step in ensuring clarity and accessibility. Let's explore an efficient way to automate this process using pydoc-markdown.

**1. Document Your Flow in Sphinx Format**
-------------------------------------------
Start by documenting your Flow in `Sphinx format`_. Need a reference? Check out `ChatFlowModule`_ for inspiration.

 Pro tip: Leverage VSCode's GitHub Copilot to expedite the documentation process.

**2. Install pydoc-markdown**
-------------------------------
Ensure you have the necessary tool installed by running the following command::
    
    pip install pydoc-markdown


**3. Navigate to Your Flow Directory**
------------------------------------------
Go to the directory containing your Flow file::

    cd <PATH_TO_YOUR_FLOW>


**4. Build the Markdown** 
------------------------------------------
Generate the Markdown documentation using pydoc-markdown. Replace <YOUR-FLOW> with the name of your Flow file (excluding the `.py` extension). 
For example, if your Flow file is named `Flow1.py`, execute the following command::


    pydoc-markdown  -p Flow1 --render-toc > README.md 


If you have multiple Flow files, consider using the following command to include all files in the documentation::


    pydoc-markdown  -I . --render-toc > README.md 


------

This process automates the generation of Markdown documentation for your Flow, streamlining the contribution process on the FlowVerse. Happy documenting! 🚀✨

.. _Sphinx format: https://sphinx-rtd-tutorial.readthedocs.io/en/latest/docstrings.html
.. _ChatFlowModule: https://huggingface.co/aiflows/ChatFlowModule/blob/main/ChatAtomicFlow.py
