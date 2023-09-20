# Flows: Building Blocks of Reasoning and Collaborating AI

## Introduction

**Flows** is a framework for building complex reasoning and interaction patterns on top of LLM and tools. It provides a set of basic interaction patterns, such as:

- **sequential execution**: execute a set of LLMs or tools in a sequence
- **selection execution**: execute one of a set of LLMs or tools based on a runtime condition
- **circulation execution**: execute a set of LLMs or tools in a loop until a runtime condition is met

These patterns are composable, allowing you to build complex flows of execution.

## Get started

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

## Tutorials

A series of guides that explain how to build your own `Flow`, use our visualization toolkit to debug it, and finally upload it to the Flow-verse to share it with the community.

- [Flows Tutorial](docs/tutorials/main.md)

## Contributing

There are two ways to contribute to the project: by contributing to the **codebase** or by contributing to the **Flow-verse**.

- **Codebase**: We welcome contributions to the project and accept pull requests of all sorts: documentation, code, bug fixes, etc.
- **Flow-verse**: We hope to establish flows as a platform to enable collaboration, sharing, and reusing. Uploading your work to the Flow-verse is a great way to contribute to the community and to the project.

Last but not least, if you want to prepare educational material (tutorials, videos, etc.) about flows, we would love to hear from you! We are happy to link to your content from the project website.

All Github contributors will be explicitly named in release notes of future versions of the library. If anything is unclear, confusing, or needs to be refactored, please let us know by opening an issue on the repository.
