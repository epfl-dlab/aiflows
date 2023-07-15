from copy import deepcopy

import hydra

import time

from typing import List, Dict, Optional, Any

from langchain import PromptTemplate
import langchain
from langchain.schema import HumanMessage, AIMessage, SystemMessage

from flows.base_flows.abstract import AtomicFlow

from flows.utils import logging
from flows.messages.flow_message import UpdateMessage_ChatMessage

log = logging.get_logger(__name__)

# ToDo: Add support for demonstrations


class OpenAIChatAtomicFlow(AtomicFlow):
    REQUIRED_KEYS_CONFIG = ["model_name", "generation_parameters"]
    REQUIRED_KEYS_CONSTRUCTOR = ["system_message_prompt_template",
                            "human_message_prompt_template",
                            "init_human_message_prompt_template"]

    SUPPORTS_CACHING: bool = True

    api_keys: Dict[str, str]

    system_message_prompt_template: PromptTemplate
    human_message_prompt_template: PromptTemplate

    init_human_message_prompt_template: Optional[PromptTemplate] = None
    # demonstrations: GenericDemonstrationsDataset = None
    demonstrations_response_template: PromptTemplate = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.api_keys = None

        assert self.flow_config["name"] not in [
            "system",
            "user",
            "assistant",
        ], f"Flow name '{self.flow_config['name']}' cannot be 'system', 'user' or 'assistant'"

    def set_up_flow_state(self):
        super().set_up_flow_state()
        self.flow_state["previous_messages"] = []

    @classmethod
    def _set_up_prompts(cls, config):
        kwargs = {}

        kwargs["system_message_prompt_template"] = \
            hydra.utils.instantiate(config['system_message_prompt_template'], _convert_="partial")
        kwargs["init_human_message_prompt_template"] = \
            hydra.utils.instantiate(config['init_human_message_prompt_template'], _convert_="partial")
        kwargs["human_message_prompt_template"] = \
            hydra.utils.instantiate(config['human_message_prompt_template'], _convert_="partial")

        return kwargs

    # @classmethod
    # def _set_up_demonstration_templates(cls, config):
    #     kwargs = {}
    #
    #     if "demonstrations_response_template" in config:
    #         kwargs["demonstrations_response_template"] = \
    #             hydra.utils.instantiate(config['demonstrations_response_template'], _convert_="partial")
    #
    #     return kwargs

    @classmethod
    def instantiate_from_config(cls, config):
        flow_config = deepcopy(config)

        kwargs = {"flow_config": flow_config}
        kwargs["input_data_transformations"] = cls._set_up_data_transformations(config["input_data_transformations"])
        kwargs["output_data_transformations"] = cls._set_up_data_transformations(config["output_data_transformations"])

        # ~~~ Set up prompts ~~~
        kwargs.update(cls._set_up_prompts(flow_config))

        # # ~~~ Set up demonstration templates ~~~
        # kwargs.update(cls._set_up_demonstration_templates(flow_config))

        # ~~~ Instantiate flow ~~~
        return cls(**kwargs)

    def _is_conversation_initialized(self):
        if len(self.flow_state["previous_messages"]) > 0:
            return True

        return False

    def get_input_keys(self, data: Optional[Dict[str, Any]] = None):
        """Returns the expected inputs for the flow given tshe current state and, optionally, the input data"""
        if self._is_conversation_initialized():
            return self.flow_config["input_keys"]
        else:
            return self.flow_config["init_input_keys"]

    @staticmethod
    def _get_message(prompt_template, input_data: Dict[str, Any]):
        template_kwargs = {}
        for input_variable in prompt_template.input_variables:
            template_kwargs[input_variable] = input_data[input_variable]

        msg_content = prompt_template.format(**template_kwargs)
        return msg_content

    # def _get_demonstration_query_message_content(self, sample_data: Dict):
    #     input_variables = self.query_message_prompt_template.input_variables
    #     return self.query_message_prompt_template.format(**{k: sample_data[k] for k in input_variables}), []
    #
    # def _get_demonstration_response_message_content(self, sample_data: Dict):
    #     input_variables = self.demonstrations_response_template.input_variables
    #     return self.demonstrations_response_template.format(**{k: sample_data[k] for k in input_variables}), []

    # def _add_demonstrations(self):
    #     if self.demonstrations is not None:
    #         for example in self.demonstrations:
    #             query, parents = self._get_demonstration_query_message_content(example)
    #             response, parents = self._get_demonstration_response_message_content(example)
    #
    #             self._log_chat_message(content=query,
    #                                    role=self.user_name,
    #                                    parent_message_ids=parents)
    #
    #             self._log_chat_message(content=response,
    #                                    role=self.assistant_name,
    #                                    parent_message_ids=parents)

    def _state_update_add_chat_message(self,
                                       role: str,
                                       content: str) -> None:

        # Add the message to the previous messages list
        if role == self.flow_config["system_name"]:
            self.flow_state["previous_messages"].append(SystemMessage(content=content))
        elif role == self.flow_config["user_name"]:
            self.flow_state["previous_messages"].append(HumanMessage(content=content))
        elif role == self.flow_config["assistant_name"]:
            self.flow_state["previous_messages"].append(AIMessage(content=content))
        else:
            raise Exception(f"Invalid role: `{role}`.\n"
                            f"Role should be one of: "
                            f"`{self.flow_config['system_name']}`, "
                            f"`{self.flow_config['user_name']}`, "
                            f"`{self.flow_config['assistant_name']}`")

        # Log the update to the flow messages list
        chat_message = UpdateMessage_ChatMessage(
            created_by=self.flow_config["name"],
            updated_flow=self.flow_config["name"],
            role=role,
            content=content,
        )
        self._log_message(chat_message)

    def _call(self):
        api_key = self.api_keys["openai"]

        backend = langchain.chat_models.ChatOpenAI(
            model_name=self.flow_config["model_name"],
            openai_api_key=api_key,
            **self.flow_config["generation_parameters"],
        )

        messages = self.flow_state["previous_messages"]

        _success = False
        attempts = 1
        error = None
        response = None
        while attempts <= self.flow_config['n_api_retries']:
            try:
                response = backend(messages).content
                _success = True
                break
            except Exception as e:
                log.error(
                    f"Error {attempts} in calling backend: {e}. Key used: `{api_key}`. "
                    f"Retrying in {self.flow_config['wait_time_between_retries']} seconds..."
                )
                # log.error(
                #     f"The API call raised an exception with the following arguments: "
                #     f"\n{self.flow_state['history'].to_string()}"
                # ) # ToDo: Make this message more user-friendly
                attempts += 1
                time.sleep(self.flow_config['wait_time_between_retries'])
                error = e

        if not _success:
            raise error

        return response

    def _initialize_conversation(self, input_data: Dict[str, Any]):
        # ~~~ Add the system message ~~~
        system_message_content = self._get_message(self.system_message_prompt_template, input_data)

        self._state_update_add_chat_message(content=system_message_content,
                                            role=self.flow_config["system_name"])

        # # ~~~ Add the demonstration query-response tuples (if any) ~~~
        # self._add_demonstrations()
        # self._update_state(update_data={"conversation_initialized": True})

    def _process_input(self, input_data: Dict[str, Any]):
        if self._is_conversation_initialized():
            # Construct the message using the human message prompt template
            user_message_content = self._get_message(self.human_message_prompt_template, input_data)

        else:
            # Initialize the conversation (add the system message, and potentially the demonstrations)
            self._initialize_conversation(input_data)
            # Construct the message using the query message prompt template
            user_message_content = self._get_message(self.init_human_message_prompt_template, input_data)

        self._state_update_add_chat_message(role=self.flow_config["user_name"],
                                            content=user_message_content)

    def run(self,
            input_data: Dict[str, Any]) -> Dict[str, Any]:
        # ~~~ Process input ~~~
        self._process_input(input_data)

        # ~~~ Call ~~~
        response = self._call()
        self._state_update_add_chat_message(
            role=self.flow_config["assistant_name"],
            content=response
        )

        return {"api_output": response}