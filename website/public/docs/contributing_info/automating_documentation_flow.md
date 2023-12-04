# Automating the documentation of a Flow on  the FlowVerse

Documenting your Flow is a crucial step in ensuring clarity and accessibility. Let's explore an efficient way to automate this process using pydoc-markdown.

## 1. Document Your Flow in Sphinx Format
Start by documenting your Flow in [Sphinx format]( https://sphinx-rtd-tutorial.readthedocs.io/en/latest/docstrings.html). Need a reference? Check out [ChatFlowModule](https://huggingface.co/aiflows/ChatFlowModule/blob/main/ChatAtomicFlow.py) for inspiration.

 Pro tip: Leverage VSCode's GitHub Copilot to expedite the documentation process.

## 2. Install pydoc-markdown
Ensure you have the necessary tool installed by running the following command:
```bash
pip install pydoc-markdown
```

## 3. Navigate to Your Flow Directory:
```bash 
cd <PATH_TO_YOUR_FLOW>
```

## 4. Build the Markdown
Generate the Markdown documentation using pydoc-markdown. Replace <YOUR-FLOW> with the name of your Flow file (excluding the `.py` extension). For example, if your Flow file is named `Flow1.py`, execute the following command:

```bash
pydoc-markdown  -p Flow1 --render-toc > README.md 
```

If you have multiple Flow files, consider using the following command to include all files in the documentation:

```bash
pydoc-markdown  -I . --render-toc > README.md 
```

---
This process automates the generation of Markdown documentation for your Flow, streamlining the contribution process on the FlowVerse. Happy documenting! 🚀✨