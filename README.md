[![arXiv](https://img.shields.io/badge/arXiv-2308.01285-b31b1b.svg)](https://arxiv.org/abs/2308.01285)

# Flows: Building Blocks of Reasoning and Collaborating AI

## Introduction

**Flows** is a framework for building complex reasoning and interaction patterns on top of LLM and tools. It provides a set of basic interaction patterns, such as:

- **sequential execution**: execute a set of LLMs or tools in a sequence
- **selection execution**: execute one of a set of LLMs or tools based on a runtime condition
- **circulation execution**: execute a set of LLMs or tools in a loop until a runtime condition is met

These patterns are composable, allowing you to build complex flows of execution.

## Installation

To install flows, run the following command:

```shell
git clone git@github.com:epfl-dlab/flows.git
cd flows
pip install -e .
```

## Documentation

- [Atomic Flows](docs/atomic_flow.md)
- [Composite Flows](docs/composite_flow.md)
- [caching](docs/caching.md)
- [Flow Modules](docs/flow_module_management.md)
- [logging](docs/logging.md)
- [AutoGPT](docs/autogpt.md)

## Running the experiments in the paper

The flows for reproducing the results in [paper](https://arxiv.org/pdf/2308.01285.pdf) are available in [CCFlows](https://huggingface.co/aiflows/CCFlows).

## Contributing

There are two ways to contribute to the project: by contributing to the **codebase** or by contributing to the **Flow-verse**.

- **Codebase**: We welcome contributions to the project and accept pull requests of all sorts: documentation, code, bug fixes, etc.
- **Flow-verse**: We hope to establish flows as a platform to enable collaboration, sharing, and reusing. Uploading your work to the Flow-verse is a great way to contribute to the community and to the project.

Last but not least, if you want to prepare educational material (tutorials, videos, etc.) about flows, we would love to hear from you! We are happy to link to your content from the project website.

All Github contributors will be explicitly named in release notes of future versions of the library. If anything is unclear, confusing, or needs to be refactored, please let us know by opening an issue on the repository.

# ToDo: Add information about how to use Azure backend

## Citation

This repository contains the code for the models and experiments in [Flows: Building Blocks of Reasoning and Collaborating AI](https://arxiv.org/pdf/2308.01285.pdf)

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
**Please consider citing our work, if you found the provided resources useful.**<br>
