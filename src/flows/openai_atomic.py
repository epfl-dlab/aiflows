import pprint

import colorama
import time

from typing import List, Dict, Optional

from langchain import PromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage, AIMessage, SystemMessage

from src.history import FlowHistory
from src.message_annotators import EndOfInteraction
from src.message_annotators.abstract import MessageAnnotator
from src.flows.abstract import AtomicFlow
from src.datasets import GenericDemonstrationsDataset

from src import utils
from src.messages.chat_message import ChatMessage
from src.messages.flow_message import TaskMessage
from src.utils import general_helpers

log = utils.get_pylogger(__name__)


class OpenAIChatAtomicFlow(AtomicFlow):

    def __init__(
            self,
            name: str,
            description: str,
            expected_inputs: List[str],
            expected_outputs: List[str],
            model_name: str,
            generation_parameters: Dict,
            system_message_prompt_template: PromptTemplate,
            human_message_prompt_template: PromptTemplate,
            system_name: str = "system",
            user_name: str = "user",
            assistant_name: str = "assistant",
            n_api_retries: int = 6,
            wait_time_between_retries: int = 20,
            query_message_prompt_template: Optional[PromptTemplate] = None,
            demonstrations: GenericDemonstrationsDataset = None,
            demonstrations_response_template: PromptTemplate = None,
            response_annotators: Optional[Dict[str, MessageAnnotator]] = None,
            verbose: Optional[bool] = False,
            **kwargs,
    ):
        super().__init__(
            name=name,
            description=description,
            expected_inputs=expected_inputs,
            expected_outputs=expected_outputs,
            verbose=verbose,
        )

        assert self.name not in [
            "system",
            "user",
            "assistant",
        ], f"Flow name '{self.name}' cannot be 'system', 'user' or 'assistant'"

        # ~~~ Model generation ~~~
        self.model_name = model_name
        self.generation_parameters = generation_parameters

        # ~~~ Prompting ~~~
        self.system_message_prompt_template = system_message_prompt_template
        self.human_message_prompt_template = human_message_prompt_template
        self.query_message_prompt_template = query_message_prompt_template

        # Demonstrations
        self.demonstrations = demonstrations
        self.demonstrations_response_template = demonstrations_response_template

        # ~~~ Response parsing ~~~
        self.response_annotators = response_annotators if response_annotators else {}

        # ~~~ API formatting ~~~
        self.system_name = system_name
        self.user_name = user_name
        self.assistant_name = assistant_name

        # ~~~ Fault tolerance ~~~
        self.n_api_retries = n_api_retries
        self.wait_time_between_retries = wait_time_between_retries

    def initialize(self):
        self.state = {}
        self.history = FlowHistory()
        self.state["flow_run_id"] = general_helpers.create_unique_id()
        self._update_state(update_data={"conversation_initialized": False})

    def expected_inputs_given_state(self):
        conv_init = False
        if "conversation_initialized" in self.state:
            conv_init = self.state["conversation_initialized"].content

        if conv_init:
            return ["query"]
        else:
            return self.expected_inputs

    @staticmethod
    def _get_message(prompt_template, input_message: TaskMessage):

        template_kwargs = {}
        for input_variable in prompt_template.input_variables:
            template_kwargs[input_variable] = input_message.data[input_variable]

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

    def _response_parsing(self, response: str, expected_keys: List[str]):
        target_annotators = [ra for _, ra in self.response_annotators.items() if ra.key in expected_keys]

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
                                       message_creator=self.state["user_name"],
                                       parent_message_ids=parents)

                self._log_chat_message(content=response,
                                       message_creator=self.state["assistant_name"],
                                       parent_message_ids=parents)

    def _log_chat_message(self, message_creator: str, content: str, parent_message_ids: List[str] = None):
        chat_message = ChatMessage(
            message_creator=message_creator,
            parent_message_ids=parent_message_ids,
            flow_runner=self.name,
            flow_run_id=self.state["flow_run_id"],
            content=content
        )
        return self._log_message(chat_message)

    def _initialize_conversation(self, input_message: TaskMessage):
        # ~~~ Add the system message ~~~
        system_message_content = self._get_message(self.state["system_message_prompt_template"], input_message)

        self._log_chat_message(content=system_message_content,
                               message_creator=self.system_name,
                               parent_message_ids=[input_message.message_id])

        # ~~~ Add the demonstration query-response tuples (if any) ~~~
        self._add_demonstrations()
        self._update_state(update_data={"conversation_initialized": True})

    def end_of_interaction_key(self):
        for _, ra in self.response_annotators.items():
            if type(ra) == EndOfInteraction:
                return ra.key
        return None

    def get_conversation_messages(self, flow_run_id: str, message_format: Optional[str] = None):
        assert message_format is None or message_format in [
            "open_ai"
        ], f"Currently supported conversation message formats: 'open_ai'. '{message_format}' is not supported"

        messages = [message for message in self.history.messages
                    if message.flow_run_id == flow_run_id and isinstance(message, ChatMessage)]

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
        api_key = self.state["api_key"]

        backend = ChatOpenAI(
            model_name=self.model_name,
            openai_api_key=api_key,
            **self.generation_parameters,
            # model_kwargs=self.generation_parameters
        )

        messages = self.get_conversation_messages(
            flow_run_id=self.state['flow_run_id'],
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
                    f"\n{self.history.to_string(self.get_conversation_messages(self.state['flow_run_id']), show_dict=False)}"
                )
                attempts += 1
                time.sleep(self.wait_time_between_retries)
                error = e

        if not _success:
            raise error

        if self.verbose:
            messages_str = self.history.to_string(
                self.get_conversation_messages(self.state['flow_run_id']), show_dict=False
            )
            log.info(
                f"\n{colorama.Fore.MAGENTA}~~~ History [{self.name}] ~~~\n"
                f"{colorama.Style.RESET_ALL}{messages_str}"
            )

        return response

    def _prepare_conversation(self, input_message):
        conv_init = False
        if "conversation_initialized" in self.state:
            conv_init = self.state["conversation_initialized"]

        if conv_init:
            # ~~~ Check that the message has a `query` field ~~~

            user_message_content = self.human_message_prompt_template.format(query=input_message.data["query"])

        else:
            self._initialize_conversation(input_message)

            user_message_content = self._get_message(self.query_message_prompt_template, input_message)

        self._log_chat_message(message_creator=self.user_name,
                               content=user_message_content,
                               parent_message_ids=[input_message.message_id])

        if self.state["dry_run"]:
            messages = self.get_conversation_messages(self.state["flow_run_id"])
            messages_str = self.history.to_string(messages, show_dict=False)
            log.info(
                f"\n{colorama.Fore.MAGENTA}~~~ Messages [{self.name} -- {self.state['flow_run_id']}] ~~~\n"
                f"{colorama.Style.RESET_ALL}{messages_str}"
            )
            exit(0)

    def run(self, task_message: TaskMessage):
        # ~~~ Chat-specific preparation ~~~
        self._prepare_conversation(task_message)

        # ~~~ Call ~~~
        response = self._call()
        answer_message = self._log_chat_message(message_creator=self.assistant_name,
                                                content=response,
                                                parent_message_ids=[task_message.message_id])

        # ~~~ Response parsing ~~~
        parsed_outputs = self._response_parsing(response=response, expected_keys=self.state["expected_output_keys"])
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
