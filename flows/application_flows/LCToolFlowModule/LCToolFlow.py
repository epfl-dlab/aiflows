from __future__ import annotations
from copy import deepcopy
from typing import Any, Dict

import hydra
from langchain.tools import BaseTool

from flows.base_flows import AtomicFlow


class LCToolFlow(AtomicFlow):
    REQUIRED_KEYS_CONFIG = ["backend"]

    # KEYS_TO_IGNORE_WHEN_RESETTING_NAMESPACE = {"backend"}，TODO this will overwrite the KEYS_TO_IGNORE_WHEN_RESETTING_NAMESPACE in base_flows.py

    SUPPORTS_CACHING: bool = False

    backend: BaseTool

    def __init__(self, backend: BaseTool, **kwargs) -> None:
        super().__init__(**kwargs)
        self.backend = backend
        
    @classmethod
    def _set_up_backend(cls, config: Dict[str, Any]) -> BaseTool:
        if config["_target_"].startswith("."):
            # assumption: cls is associated with relative data_transformation_configs
            # for example, CF_Code and CF_Code.yaml should be in the same directory,
            # and all _target_ in CF_Code.yaml should be relative
            cls_parent_module = ".".join(cls.__module__.split(".")[:-1])
            config["_target_"] = cls_parent_module + config["_target_"]
        tool = hydra.utils.instantiate(config, _convert_="partial")

        return tool

    @classmethod
    def instantiate_from_config(cls, config: Dict[str, Any]) -> LCToolFlow:
        flow_config = deepcopy(config)

        kwargs = {"flow_config": flow_config}
        kwargs["input_data_transformations"] = cls._set_up_data_transformations(config["input_data_transformations"])
        kwargs["output_data_transformations"] = cls._set_up_data_transformations(config["output_data_transformations"])

        # ~~~ Set up LangChain backend ~~~
        kwargs["backend"] = cls._set_up_backend(config["backend"])

        # ~~~ Instantiate flow ~~~
        return cls(**kwargs)

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        observation = self.backend.run(tool_input=input_data)

        return {"observation": observation}

