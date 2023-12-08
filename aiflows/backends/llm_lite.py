from litellm import completion, embedding
from typing import Any, List, Dict, Iterable, Union, Optional, Tuple
import time
from aiflows.backends.api_info import ApiInfo
import multiprocessing


def merge_delta_to_stream(merged_stream, delta):
    """Merges a delta to a stream. It is used to merge the deltas from the streamed response of the litellm library.

    :param merged_stream: The already merged stream
    :type merged_stream: Dict[str, Any]
    :param delta: The delta to merge with the merge_stream
    :type delta: Dict[str, Any]
    :return: The merged stream
    :rtype: Dict[str, Any]
    """
    for delta_key, delta_value in delta.items():
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
            # delta is initialy a class (Delta) and must be converted to a dictionary (using the content attribute)
            if "content" not in choice["delta"]:
                continue
            delta = {"content": choice["delta"]["content"]}
            merged_streams[int(choice["index"])] = merge_delta_to_stream(merged_streams[int(choice["index"])], delta)
    return merged_streams


class LiteLLMBackend:
    """This class is a wrapper around the litellm library. It allows to use multiple API keys and to switch between them
    automatically when one is exhausted.

    :param api_infos: A list of ApiInfo objects, each containing the information about one API key
    :type api_infos: List[ApiInfo]
    :param model_name: The name of the model to use. Can be a string or a dictionary from API to model name
    :type model_name: Union[str, Dict[str, str]]
    :param wait_time_per_key: The minimum time to wait between two calls on the same API key
    :type wait_time_per_key: int
    :param embeddings_call: Whether to use the embedding API or the completion API
    :type embeddings_call: bool
    :param kwargs: Additional parameters to pass to the litellm library
    :type kwargs: Any
    """

    # last call time per key must be shared between all instances of the class (mulitple threads and objects can share the same apis keys)
    __last_call_per_key: Dict[str, float] = {}
    # ensure that the last call time per key is not modified or read by multiple threads of objects at the same time
    __read_write_lock: multiprocessing.Lock = multiprocessing.Lock()

    def __init__(self, api_infos, model_name, **kwargs):
        """Constructor method"""
        self.model_name = model_name
        self.params = kwargs
        self.__waittime_per_key = (
            self.params.pop("wait_time_per_key")
            if "wait_time_per_key" in self.params
            else self.params.get("wait_time_per_key", 6)
        )
        self.embeddings_call = (
            self.params.pop("embeddings_call")
            if "embeddings_call" in self.params
            else self.params.get("embeddings_call", False)
        )

        api_infos = api_infos if isinstance(api_infos, list) else [api_infos]
        api_infos = [info if isinstance(info, ApiInfo) else ApiInfo(**info) for info in api_infos]
        LiteLLMBackend._api_information_sanity_check(api_infos)

        # the last_call_per_key of each api key of the instantiated object
        object_last_call_per_key = {
            LiteLLMBackend.make_unique_api_info_key(api_info): time.time() - self.__waittime_per_key
            for api_info in api_infos
        }
        # Update the last_call_per_key of the class with the last_call_per_key of the instantiated object (updates only the keys that are not already in the class variable)
        LiteLLMBackend._prioritized_merge_last_call_per_key(object_last_call_per_key)

        # A dictorary containing the api info of the object (key is the backend_used + api_key) value is the api_info object
        # e.g {"openai-1234": ApiInfo(backend_used="openai", api_key="1234", api_base="https://api.openai.com", api_version="v1")}
        self.api_infos = {LiteLLMBackend.make_unique_api_info_key(api_info): api_info for api_info in api_infos}

    @staticmethod
    def make_unique_api_info_key(api_info: ApiInfo):
        """Makes a unique key for the api_info object

        :param api_info: The api_info object
        :type api_info: ApiInfo
        :return: The unique key for the api_info object
        :rtype: str
        """
        return str(api_info.backend_used + api_info.api_key)

    @classmethod
    def _prioritized_merge_last_call_per_key(cls, dict2):
        """Updates the last_call_per_key of the class with the last_call_per_key of the instantiated object (updates only the keys that are not already in the class variable)

        :param dict2: The last_call_per_key of the instantiated object
        :type dict2: Dict[str, float]
        """
        # Ensures read and write are not done at the same time
        with cls.__read_write_lock:
            LiteLLMBackend.__last_call_per_key = {**dict2, **LiteLLMBackend.__last_call_per_key}

    @classmethod
    def _get_last_call_per_key(cls, keys: Iterable[str] = None):
        """Gets the last_call_per_key of the class variable. If keys is None, returns the whole dictionary, otherwise returns the values of the keys in the list keys

        :param keys: The keys to return the values of, defaults to None
        :type keys: List[str], optional
        :return: The last_call_per_key of the class variable (or the values of the keys in the list keys)
        :rtype: Dict[str, float]
        """
        # Ensures read and write are not done at the same time
        with cls.__read_write_lock:
            if keys is None:
                return cls.__last_call_per_key
            else:
                return {key: value for key, value in cls.__last_call_per_key.items() if key in keys}

    @classmethod
    def _update_time_last_call_per_key(cls, key: str):
        """Updates the time of last_call_per_key of the class variable for the provided key

        :param key: The key to update the last_call_per_key of
        :type key: str
        """
        # Ensures read and write are not done at the same time
        with cls.__read_write_lock:
            cls.__last_call_per_key.update({key: time.time()})

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
        # Gets the last call per key of the object (but only for the apikeys that are in the class variable)
        object_last_call_per_key = LiteLLMBackend._get_last_call_per_key(keys=self.api_infos.keys())

        # Retrieve key of api key that was used the least recently
        api_key_idx = min(object_last_call_per_key, key=object_last_call_per_key.get)
        # Check how long ago the api key was used
        last_call_on_key = time.time() - object_last_call_per_key[api_key_idx]

        # Check if we need to wait
        good_to_go = last_call_on_key > self.__waittime_per_key

        # If we need to wait, wait until we do
        if not good_to_go:
            time.sleep(self.__waittime_per_key - last_call_on_key)
            return self._choose_next_api_key()

        # Update the last call time
        LiteLLMBackend._update_time_last_call_per_key(api_key_idx)
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
            assert (
                api_backend in self.model_name.keys()
            ), f"A model has not been specified for the backend '{api_backend}'.Currently specified backend to model mappings: {self.model_name}"
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

        api_key_info = self.get_key()

        litellm_api_info = self._get_model_and_api_dict(api_key_info)

        merged_kwargs = {**kwargs, **litellm_api_info}

        return self._call(**merged_kwargs)
