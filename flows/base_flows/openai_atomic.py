import pprint
import hydra

import colorama
import time

from typing import List, Dict, Optional, Any

from langchain import PromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage, AIMessage, SystemMessage

from flows.message_annotators.abstract import MessageAnnotator
from flows.base_flows.abstract import AtomicFlow
from flows.datasets import GenericDemonstrationsDataset

from flows import utils
from flows.messages.chat_message import ChatMessage

log = utils.get_pylogger(__name__)


class OpenAIChatAtomicFlow(AtomicFlow):
    model_name: str
    generation_parameters: Dict

    system_message_prompt_template: PromptTemplate
    human_message_prompt_template: PromptTemplate

    system_name: str = "system"
    user_name: str = "user"
    assistant_name: str = "assistant"

    n_api_retries: int = 6
    wait_time_between_retries: int = 20

    query_message_prompt_template: Optional[PromptTemplate] = None
    demonstrations: GenericDemonstrationsDataset = None
    demonstrations_response_template: PromptTemplate = None
    response_annotators: Optional[Dict[str, MessageAnnotator]] = None

    def __init__(self, **kwargs):
        # ~~~ Model generation ~~~
        if "model_name" not in kwargs:
            raise KeyError

        if "generation_parameters" not in kwargs:
            raise KeyError

        # ~~~ Prompting ~~~
        if "system_message_prompt_template" not in kwargs:
            raise KeyError

        if "human_message_prompt_template" not in kwargs:
            raise KeyError

        if "query_message_prompt_template" not in kwargs:
            kwargs["query_message_prompt_template"] = None

        # Demonstrations
        if "demonstrations" not in kwargs:
            kwargs["demonstrations"] = None

        if "demonstrations_response_template" not in kwargs:
            kwargs["demonstrations_response_template"] = None

        # ~~~ Response parsing ~~~
        if "response_annotators" not in kwargs:
            kwargs["response_annotators"] = {}

        # ~~~ API formatting ~~~
        if "system_name" not in kwargs:
            kwargs["system_name"] = "system"

        if "user_name" not in kwargs:
            kwargs["user_name"] = "user"

        if "assistant_name" not in kwargs:
            kwargs["assistant_name"] = "assistant"

        # ~~~ Fault tolerance ~~~
        if "n_api_retries" not in kwargs:
            kwargs["n_api_retries"] = 6

        if "wait_time_between_retries" not in kwargs:
            kwargs["wait_time_between_retries"] = 20

        super().__init__(**kwargs)
        self._instantiate()

        assert self.name not in [
            "system",
            "user",
            "assistant",
        ], f"Flow name '{self.name}' cannot be 'system', 'user' or 'assistant'"

    def _instantiate(self):
        # ~~~ Instantiate prompts ~~~
        self.system_message_prompt_template = \
            hydra.utils.instantiate(self.flow_config['system_message_prompt_template'], _convert_="partial")
        self.query_message_prompt_template = \
            hydra.utils.instantiate(self.flow_config['query_message_prompt_template'], _convert_="partial")
        if self.flow_config["human_message_prompt_template"] is not None:
            self.human_message_prompt_template = \
                hydra.utils.instantiate(self.flow_config['human_message_prompt_template'], _convert_="partial")

        # ~~~ Instantiate response annotators ~~~
        if self.flow_config["response_annotators"] and len(self.flow_config["response_annotators"]) > 0:
            for key, config in self.flow_config["response_annotators"].items():
                self.response_annotators[key] = hydra.utils.instantiate(config, _convert_="partial")

    def is_initialized(self):
        conv_init = False
        if "conversation_initialized" in self.flow_state:
            conv_init = self.flow_state["conversation_initialized"].content
        return conv_init

    def expected_inputs_given_state(self):
        if self.is_initialized():
            return ["query"]
        else:
            return self.expected_inputs

    @staticmethod
    def _get_message(prompt_template, input_data: Dict[str, Any]):
        template_kwargs = {}
        for input_variable in prompt_template.input_variables:
            template_kwargs[input_variable] = input_data[input_variable]

        msg_content = prompt_template.format(**template_kwargs)
        return msg_content

    def _get_demonstration_query_message_content(self, sample_data: Dict):
        return self.query_message_prompt_template.format(**sample_data), []

    def _get_demonstration_response_message_content(self, sample_data: Dict):
        return self.demonstrations_response_template.format(**sample_data), []

    def _get_annotator_with_key(self, key: str):
        for _, ra in self.response_annotators.items():
            if ra.key == key:
                return ra

    def _response_parsing(self, response: str, expected_outputs: List[str]):
        target_annotators = [ra for _, ra in self.response_annotators.items() if ra.key in expected_outputs]

        parsed_outputs = {}
        for ra in target_annotators:
            parsed_out = ra(response)
            parsed_outputs.update(parsed_out)
        return parsed_outputs

    def _add_demonstrations(self):
        if self.demonstrations is not None:
            for example in self.demonstrations:
                query, parents = self._get_demonstration_query_message_content(example)
                response, parents = self._get_demonstration_response_message_content(example)

                self._log_chat_message(content=query,
                                       message_creator=self.user_name,
                                       parent_message_ids=parents)

                self._log_chat_message(content=response,
                                       message_creator=self.assistant_name,
                                       parent_message_ids=parents)

    def _log_chat_message(self, message_creator: str, content: str, parent_message_ids: List[str] = None):
        chat_message = ChatMessage(
            message_creator=message_creator,
            parent_message_ids=parent_message_ids,
            flow_runner=self.name,
            flow_run_id=self.flow_run_id,
            content=content
        )
        return self._log_message(chat_message)

    def _initialize_conversation(self, input_data: Dict[str, Any]):
        # ~~~ Add the system message ~~~
        system_message_content = self._get_message(self.system_message_prompt_template, input_data)

        self._log_chat_message(content=system_message_content,
                               message_creator=self.system_name)

        # ~~~ Add the demonstration query-response tuples (if any) ~~~
        self._add_demonstrations()
        self._update_state(update_data={"conversation_initialized": True})

    def get_conversation_messages(self, message_format: Optional[str] = None):
        assert message_format is None or message_format in [
            "open_ai"
        ], f"Currently supported conversation message formats: 'open_ai'. '{message_format}' is not supported"

        messages = self.flow_state["history"].get_chat_messages()

        if message_format is None:
            return messages

        elif message_format == "open_ai":
            processed_messages = []

            for message in messages:
                if message.message_creator == self.system_name:
                    processed_messages.append(SystemMessage(content=message.content))
                elif message.message_creator == self.assistant_name:
                    processed_messages.append(AIMessage(content=message.content))
                elif message.message_creator == self.user_name:
                    processed_messages.append(HumanMessage(content=message.content))
                else:
                    raise ValueError(f"Unknown name: {message.message_creator}")
            return processed_messages
        else:
            raise ValueError(f"Unknown message format: {message_format}")

    def _call(self):
        api_key = self.flow_state["api_key"]

        backend = ChatOpenAI(
            model_name=self.model_name,
            openai_api_key=api_key,
            **self.generation_parameters,
        )

        messages = self.get_conversation_messages(
            message_format="open_ai"
        )

        _success = False
        attempts = 1
        error = None
        response = None
        while attempts <= self.n_api_retries:
            try:
                response = backend(messages).content
                _success = True
                break
            except Exception as e:
                log.error(
                    f"Error {attempts} in calling backend: {e}. Key used: `{api_key}`. "
                    f"Retrying in {self.wait_time_between_retries} seconds..."
                )
                log.error(
                    f"API call raised Exception with the following arguments arguments: "
                    f"\n{self.flow_state['history'].to_string()}"
                )
                attempts += 1
                time.sleep(self.wait_time_between_retries)
                error = e

        if not _success:
            raise error

        if self.verbose:
            messages_str = self.flow_state["history"].to_string()
            log.info(
                f"\n{colorama.Fore.MAGENTA}~~~ History [{self.name}] ~~~\n"
                f"{colorama.Style.RESET_ALL}{messages_str}"
            )

        return response

    def _prepare_conversation(self, input_data: Dict[str, Any]):
        if self.is_initialized():
            # ~~~ Check that the message has a `query` field ~~~
            user_message_content = self.human_message_prompt_template.format(query=input_data["query"])

        else:
            self._initialize_conversation(input_data)
            user_message_content = self._get_message(self.query_message_prompt_template, input_data)

        self._log_chat_message(message_creator=self.user_name,
                               content=user_message_content)

        # if self.flow_state["dry_run"]:
        #     messages_str = self.flow_state["history"].to_string()
        #     log.info(
        #         f"\n{colorama.Fore.MAGENTA}~~~ Messages [{self.name} -- {self.flow_run_id}] ~~~\n"
        #         f"{colorama.Style.RESET_ALL}{messages_str}"
        #     )
        #     exit(0)

    def run(self, input_data: Dict[str, Any], expected_outputs: List[str]) -> Dict[str, Any]:
        # ~~~ Chat-specific preparation ~~~
        self._prepare_conversation(input_data)

        # ~~~ Call ~~~
        response = self._call()
        answer_message = self._log_chat_message(
            message_creator=self.assistant_name,
            content=response
        )

        # ~~~ Response parsing ~~~
        parsed_outputs = self._response_parsing(
            response=response,
            expected_outputs=expected_outputs
        )
        self._update_state(update_data=parsed_outputs)

        if self.verbose:
            parsed_output_messages_str = pprint.pformat({k: m for k, m in parsed_outputs.items()},
                                                        indent=4)
            log.info(
                f"\n{colorama.Fore.MAGENTA}~~~ "
                f"Response [{answer_message.message_creator} -- "
                f"{answer_message.message_id} -- "
                f"{answer_message.flow_run_id}] ~~~"
                f"\n{colorama.Fore.YELLOW}Content: {answer_message}{colorama.Style.RESET_ALL}"
                f"\n{colorama.Fore.YELLOW}Parsed Outputs: {parsed_output_messages_str}{colorama.Style.RESET_ALL}"
            )

        # ~~~ The final answer should be in self.flow_state, thus allow_class_namespace=False ~~~
        return self._get_keys_from_state(keys=expected_outputs, allow_class_namespace=False)
