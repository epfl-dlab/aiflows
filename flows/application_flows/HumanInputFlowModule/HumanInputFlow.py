from copy import deepcopy
from typing import List, Dict, Any, Optional

import hydra
from langchain import PromptTemplate

from flows.base_flows import AtomicFlow
from flows.messages import UpdateMessage_Generic

from flows.utils import logging

log = logging.get_logger(__name__)


class HumanInputFlow(AtomicFlow):
    REQUIRED_KEYS_CONFIG = ["request_multi_line_input_flag"]

    query_message_prompt_template: PromptTemplate = None

    __default_flow_config = {
        "end_of_input_string": "EOI",
        "input_keys": [],
        "description": "A flow that asks the user for input.",
        "query_message_prompt_template": {
            "_target_": "langchain.PromptTemplate",
            "partial_variables": {},
            "template_format": "jinja2"
        }
    }

    def __init__(self, query_message_prompt_template, **kwargs):
        super().__init__(**kwargs)
        self.query_message_prompt_template = query_message_prompt_template

    @classmethod
    def _set_up_prompts(cls, config):
        kwargs = {}

        kwargs["query_message_prompt_template"] = \
            hydra.utils.instantiate(config['query_message_prompt_template'], _convert_="partial")

        return kwargs

    @classmethod
    def instantiate_from_config(cls, config):
        flow_config = deepcopy(config)

        kwargs = {"flow_config": flow_config}
        kwargs["input_data_transformations"] = cls._set_up_data_transformations(config["input_data_transformations"])
        kwargs["output_data_transformations"] = cls._set_up_data_transformations(config["output_data_transformations"])

        # ~~~ Set up prompts ~~~
        kwargs.update(cls._set_up_prompts(flow_config))

        # ~~~ Instantiate flow ~~~
        return cls(**kwargs)


    @staticmethod
    def _get_message(prompt_template, input_data: Dict[str, Any]):
        template_kwargs = {}
        for input_variable in prompt_template.input_variables:
            template_kwargs[input_variable] = input_data[input_variable]

        msg_content = prompt_template.format(**template_kwargs)
        return msg_content

    def _read_input(self):
        if not self.flow_config["request_multi_line_input_flag"]:
            log.info("Please enter you single-line response and press enter.")
            human_input = input()
            return human_input

        end_of_input_string = self.flow_config["end_of_input_string"]
        log.info(f"Please enter your multi-line response below. "
                 f"To submit the response, write `{end_of_input_string}` on a new line and press enter.")

        content = []
        while True:
            line = input()
            if line == self.flow_config["end_of_input_string"]:
                break
            content.append(line)
        human_input = "\n".join(content)
        return human_input

    def run(self,
            input_data: Dict[str, Any]) -> Dict[str, Any]:

        query_message = self._get_message(self.query_message_prompt_template, input_data)
        state_update_message = UpdateMessage_Generic(
            created_by=self.flow_config['name'],
            updated_flow=self.flow_config["name"],
            data={"query_message": query_message},
        )
        self._log_message(state_update_message)

        log.info(query_message)
        human_input = self._read_input()

        return {"human_input": human_input}
