from typing import Dict, Any

import copy
import yaml


class FlowConfig:
    def __init__(
        self,
        name: str,
        description: str = None,
        input_keys: list = None,
        output_keys: list = None,
        input_data_transformations: list = None,
        output_data_transformations: list = None,
        enable_cache: bool = False,
        keys_to_ignore_for_hash: list = None,
        private_keys: list = None,
        keep_raw_response: bool = False,
    ):
        self.name = name
        self.description = description
        self.input_keys = input_keys
        self.output_keys = output_keys
        self.input_data_transformations = input_data_transformations or []
        self.output_data_transformations = output_data_transformations or []
        self.enable_cache = enable_cache
        self.keys_to_ignore_for_hash = keys_to_ignore_for_hash or []
        self.private_keys = private_keys or []
        self.keep_raw_response = keep_raw_response

    @classmethod
    def from_dict(cls, config: dict):
        return cls(**config)

    def to_dict(self):
        return {
            "name": self.name,
            "description": self.description,
            "input_keys": self.input_keys,
            "output_keys": self.output_keys,
            "input_data_transformations": self.input_data_transformations,
            "output_data_transformations": self.output_data_transformations,
            "enable_cache": self.enable_cache,
            "keep_raw_response": self.keep_raw_response,
        }

    @classmethod
    def from_yaml(cls, path: str):
        with open(path, "r") as f:
            config = yaml.safe_load(f)
        cls.from_dict(config)

    def to_yaml(self, path: str):
        with open(path, "w") as f:
            yaml.dump(self.to_dict(), f)

    def __getitem__(self, item):
        return getattr(self, item)

    def merge(self, other_config: Dict[str, Any]):
        """
        Merge the other_config into this config, and return the merged config.
        """

        # merge the two configs
        self_dict = copy.deepcopy(self).to_dict()
        merged_dict = self_dict.update(other_config)
        return FlowConfig.from_dict(merged_dict)


class CompositeFlowConfig(FlowConfig):
    def __init__(self, subflows_configs, **kwargs):
        super().__init__(**kwargs)
        self.subflows_configs = subflows_configs

    def from_dict(self, config: dict):
        super().from_dict(config)
        self.subflows_configs = config["subflows_configs"]

    def to_dict(self):
        return {**super().to_dict(), "subflows_configs": self.subflows_configs}


class CircularFlowConfig(CompositeFlowConfig):
    def __init__(self, max_rounds, reset_every_round, early_exit_key, **kwargs):
        super().__init__(**kwargs)
        self.max_rounds = max_rounds
        self.reset_every_round = reset_every_round
        self.early_exit_key = early_exit_key

    def from_dict(self, config: dict):
        super().from_dict(config)
        self.max_rounds = config["max_rounds"]
        self.reset_every_round = config["reset_every_round"]
        self.early_exit_key = config["early_exit_key"]

    def to_dict(self):
        return {
            **super().to_dict(),
            "max_rounds": self.max_rounds,
            "reset_every_round": self.reset_every_round,
            "early_exit_key": self.early_exit_key,
        }
