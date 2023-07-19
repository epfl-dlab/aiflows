import copy
from abc import ABC
from typing import List, Tuple, Dict, Optional

import hydra

from flows.base_flows import Flow


class CompositeFlow(Flow, ABC):
    REQUIRED_KEYS_CONFIG = ["subflows_config"]
    REQUIRED_KEYS_CONSTRUCTOR = ["flow_config", "subflows", "subflows_dict"]

    subflows: List[Tuple[str, Flow]]
    subflows_dict: Dict[str, Flow]

    def __init__(
            self,
            **kwargs
    ):
        super().__init__(**kwargs)

    def _call_flow_from_state(
            self,
            flow_to_call: Flow,
            search_class_namespace_for_inputs: bool = False,
            keys: Optional[List[str]] = None
    ):
        """A helper function that calls a given flow by extracting the input data from the state of the current flow."""
        # ~~~ Prepare the data for the call ~~~
        api_keys = getattr(self, 'api_keys', None)
        input_data = self._fetch_state_attributes_by_keys(
            keys=None, # set to be None to fetch all keys
            allow_class_attributes=search_class_namespace_for_inputs
        )
        # print(f"keys: {keys}, input_data: {input_data}, flow_to_call: {flow_to_call}")
        input_message = flow_to_call.package_input_message(data_dict=input_data,
                                                           src_flow=self,
                                                           api_keys=api_keys)

        # ~~~ Execute the call ~~~
        output_message = flow_to_call(input_message)
        # print(f"output_message: {output_message}")
        # ~~~ Logs the output message to history ~~~
        self._log_message(output_message)

        return output_message

    def _get_subflow(self, subflow_name: str) -> Optional[Flow]:
        """Returns the subflow with the given name"""
        return self.subflows_dict.get(subflow_name, None)

    @classmethod
    def _set_up_subflows(cls, config):
        subflows = []  # Dictionaries are ordered in Python 3.7+
        subflows_dict = dict()
        subflows_config = config["subflows_config"]

        for subflow_config in subflows_config:
            # Let's use hydra for now
            # subflow_config["_target_"] = ".".join([
            #     flow_verse.loading.DEFAULT_FLOW_MODULE_FOLDER,
            #     subflow_config.pop("class"),
            #     cls.instantiate_from_default_config.__name__
            # ])
            if "_target_" in subflow_config:
                if subflow_config["_target_"].startswith("."):
                    cls_parent_module = ".".join(cls.__module__.split(".")[:-1])
                    subflow_config["_target_"] = cls_parent_module + subflow_config["_target_"]

                flow_obj = hydra.utils.instantiate(subflow_config, _convert_="partial", _recursive_=False)
                subflows.append((flow_obj.flow_config["name"], flow_obj))
                subflows_dict[flow_obj.flow_config["name"]] = flow_obj

            elif "_reference_" in subflow_config:
                flow_obj = subflows_dict[subflow_config["_reference_"]]
                subflows.append((flow_obj.flow_config["name"], flow_obj))

        return subflows, subflows_dict

    @classmethod
    def instantiate_from_config(cls, config):
        flow_config = copy.deepcopy(config)

        kwargs = {"flow_config": copy.deepcopy(flow_config)}
        kwargs["subflows"], kwargs["subflows_dict"] = cls._set_up_subflows(flow_config)
        kwargs["input_data_transformations"] = cls._set_up_data_transformations(config["input_data_transformations"])
        kwargs["output_data_transformations"] = cls._set_up_data_transformations(config["output_data_transformations"])

        return cls(**kwargs)

    def _to_string(self, indent_level=0):
        """Generates a string representation of the flow"""
        indent = "\t" * indent_level
        name = self.flow_config.get("name", "unnamed")
        description = self.flow_config.get("description", "no description")
        input_keys = self.flow_config.get("input_keys", "no input keys")
        output_keys = self.flow_config.get("output_keys", "no output keys")
        class_name = self.__class__.__name__
        subflows_repr = "\n".join([f"{subflow._to_string(indent_level=indent_level + 1)}"
                                   for subflow in [flow for _, flow in self.subflows]])

        entries = [
            f"{indent}Name: {name}",
            f"{indent}Class name: {class_name}",
            f"{indent}Type: {self.type()}",
            f"{indent}Description: {description}",
            f"{indent}Input keys: {input_keys}",
            f"{indent}Output keys: {output_keys}",
            f"{indent}Subflows:",
            f"{subflows_repr}"
        ]
        return "\n".join(entries)

    @classmethod
    def type(cls):
        return "CompositeFlow"
