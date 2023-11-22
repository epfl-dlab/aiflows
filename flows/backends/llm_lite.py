from litellm import completion, embedding
from typing import Any, List, Dict, Union, Optional, Tuple
import time
from flows.backends.api_info import ApiInfo


def merge_delta_to_stream(merged_stream, delta):
    """Merges a delta to a stream. It is used to merge the deltas from the streamed response of the litellm library.
    
    :param merged_stream: The already merged stream
    :type merged_stream: Dict[str, Any]
    :param delta: The delta to merge with the merge_stream
    :type delta: Dict[str, Any]
    :return: The merged stream
    :rtype: Dict[str, Any]
    """
    delta_dict = delta.__dict__ if not isinstance(delta, dict) else delta
    for delta_key, delta_value in delta_dict.items():
        if isinstance(delta_value, dict):
            if delta_key in merged_stream:
                merge_delta_to_stream(merged_stream[delta_key], delta_value)
            else:
                merged_stream[delta_key] = delta_value

        else:
            if delta_key in merged_stream:
                merged_stream[delta_key] += delta_value
            else:
                merged_stream[delta_key] = delta_value
    return merged_stream


def merge_streams(streamed_response, n_chat_completion_choices):
    """Merges the streamed response returned from the litellm library. It is used when the stream parameter is set to True.
    
    :param streamed_response: The streamed response returned from the litellm library
    :type streamed_response: List[Dict[str, Any]]
    :param n_chat_completion_choices: The number of chat completion choices (n parameter in the completion function)
    :type n_chat_completion_choices: int
    :return: The merged streams
    :rtype: List[Dict[str, Any]]
    """
    merged_streams = [{} for i in range(n_chat_completion_choices)]
    for chunk in streamed_response:
        if "choices" not in chunk or len(chunk["choices"]) == 0:
            continue
        # must be added for case where n > 1 (argument in completion function)
        for choice in chunk["choices"]:
            merged_streams[int(choice["index"])] = merge_delta_to_stream(merged_streams[int(choice["index"])],
                                                                         choice["delta"])
    return merged_streams


class LiteLLMBackend:
    """This class is a wrapper around the litellm library. It allows to use multiple API keys and to switch between them
    automatically when one is exhausted.
    
    :param api_information: A list of ApiInfo objects, each containing the information about one API key
    :type api_information: List[ApiInfo]
    :param model_name: The name of the model to use. Can be a string or a dictionary from API to model name
    :type model_name: Union[str, Dict[str, str]]
    :param wait_time_per_key: The minimum time to wait between two calls on the same API key
    :type wait_time_per_key: int
    :param embeddings_call: Whether to use the embedding API or the completion API
    :type embeddings_call: bool
    :param kwargs: Additional parameters to pass to the litellm library
    :type kwargs: Any
    """

    def __init__(self, api_infos, model_name, **kwargs):
        """Constructor method
        """
        self.model_name = model_name
        self.params = kwargs
        self.__waittime_per_key = self.params.pop(
            "wait_time_per_key") if "wait_time_per_key" in self.params else self.params.get("wait_time_per_key", 6)
        self.embeddings_call = self.params.pop(
            "embeddings_call") if "embeddings_call" in self.params else self.params.get("embeddings_call", False)

        api_infos = api_infos if isinstance(api_infos, list) else [api_infos]
        api_infos = [info if isinstance(info, ApiInfo) else ApiInfo(**info) for info in api_infos]
        LiteLLMBackend._api_information_sanity_check(api_infos)
        self.api_infos = api_infos

        # Initialize to now - waittime_per_key to make the class know we haven't called it recently
        self.__last_call_per_key = [time.time() - self.__waittime_per_key] * len(self.api_infos)

    @staticmethod
    def _api_information_sanity_check(api_information: List[ApiInfo]):
        """Sanity check for the api information. It checks that it is not None
        
        :param api_information: The api information to check
        :type api_information: List[ApiInfo]
        """
        assert api_information is not None, "Must provide api information!"

    def _choose_next_api_key(self) -> int:
        """Chooses the next API key to use. It chooses the one that has been used the least recently.
        
        :return: The index of the next API key to use
        :rtype: int
        """
        # Choose the next API key to use
        api_key_idx = self.__last_call_per_key.index(min(self.__last_call_per_key))
        # Check if we need to wait
        last_call_on_key = time.time() - self.__last_call_per_key[api_key_idx]
        good_to_go = last_call_on_key > self.__waittime_per_key

        # If we don't need to wait, wait until we do
        if not good_to_go:
            time.sleep(self.__waittime_per_key - last_call_on_key)
            return self._choose_next_api_key()
        # Update the last call time
        self.__last_call_per_key[api_key_idx] = time.time()
        return api_key_idx

    def _call(self, **kwargs) -> List[str]:
        """
        Calls the litellm library with the given parameters.
        
        :param kwargs: The parameters to pass to the litellm library
        :type kwargs: Any
        :return: The response from the litellm library
        :rtype: List[str]
        """

        merged_params = {**self.params, **kwargs}
        if self.embeddings_call:
            response = embedding(**merged_params)
            messages = response.data
        else:
            response = completion(**merged_params)
            if merged_params.get("stream", None):
                messages = merge_streams(response, n_chat_completion_choices=kwargs.get("n", 1))
            else:
                messages = [choice["message"] for choice in response["choices"]]
        return messages

    def _get_model_and_api_dict(self, api_key_info):
        """Gets the model and api dictionary to pass to the litellm library
        
        :param api_key_info: The api key information
        :type api_key_info: ApiInfo
        :return: The model and api dictionary
        :rtype: Dict[str, str]
        """
        api_backend = api_key_info.backend_used
        api_base = api_key_info.api_base
        api_key = api_key_info.api_key
        api_version = api_key_info.api_version

        # deals with model_name type. You can pass either a single model (usually whey you're using a single API)
        # Or a dictionary from API to model (e.g. {"azure": "azure/gpt-4", {"openai": "gpt-4"}})
        # The model names follow the naming of the litellm library
        if isinstance(self.model_name, dict):
            assert api_backend in self.model_name.keys(), \
                f"A model has not been specified for the backend '{api_backend}'.Currently specified backend to model mappings: {self.model_name}"
            model_name = self.model_name[api_backend]
        else:
            model_name = self.model_name

        litellm_api_info = {"model": model_name, "api_base": api_base, "api_version": api_version, "api_key": api_key}

        return litellm_api_info

    def get_key(self):
        """Gets the next API key to use
        
        :return: The next API key to use
        :rtype: ApiInfo
        """
        api_key_idx = self._choose_next_api_key()
        return self.api_infos[api_key_idx]

    def __call__(self, **kwargs):
        """Calls the litellm library with the given parameters. It chooses the next API key to use automatically.
        
        :param kwargs: The parameters to pass to the litellm library
        :type kwargs: Any
        :return: The response from the litellm library
        :rtype: List[str]
        """
        api_key_idx = self._choose_next_api_key()
        api_key_info = self.api_infos[api_key_idx]

        litellm_api_info = self._get_model_and_api_dict(api_key_info)

        merged_kwargs = {**kwargs, **litellm_api_info}

        return self._call(**merged_kwargs)
