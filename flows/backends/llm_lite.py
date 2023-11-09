from litellm import completion
from typing import Any, List, Dict, Union, Optional, Tuple
import time
from flows.backends.api_info import ApiInfo




def merge_delta_to_stream(merged_stream,delta):
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

def merge_streams(streamed_response,n_chat_completion_choices):
        merged_streams = [{} for i in range(n_chat_completion_choices)]
        for chunk in streamed_response:
            if "choices" not in chunk or len(chunk["choices"]) == 0:
                continue
            #must be added for case where n > 1 (argument in completion function)
            for choice in chunk["choices"]:
                merged_streams[int(choice["index"])] = merge_delta_to_stream(merged_streams[int(choice["index"])],choice["delta"])
        return merged_streams

class LiteLLMBackend:
    def __init__(self,api_infos,model_name,**kwargs):

        self.model_name = model_name
        self.params = kwargs
        self.__waittime_per_key = self.params.pop("wait_time_per_key") if "wait_time_per_key" in self.params else self.params.get("wait_time_per_key", 6)

        api_infos = api_infos if isinstance(api_infos,list) else [api_infos]
        api_infos = [ info if isinstance(info,ApiInfo) else ApiInfo(**info) for info in api_infos]
        LiteLLMBackend._api_information_sanity_check(api_infos)
        self.api_infos = api_infos
        
        
        # Initialize to now - waittime_per_key to make the class know we haven't called it recently
        self.__last_call_per_key = [time.time() - self.__waittime_per_key] * len(self.api_infos)
        
    @staticmethod
    def _api_information_sanity_check(api_information: List[ApiInfo]):
        assert api_information is not None, "Must provide api information!"
       
    def _choose_next_api_key(self) -> int:
        """
        It chooses the next API key to use, by:
        - finding the one that has been used the least recently
        - check whether we need to wait for using it or not
        - if we don't need to wait, we use this key
        - if we need to wait, we wait the appropriate amount of time and retry to find a key

        Why retry instead of using the key we were waiting for after waiting?
        Because another thread might have taken this key and another one might have become available in the meantime.

        Returns:
            api_key_index, the index of the key to using next
        """
        # ToDo: I think that @Maxime mentioned that Graham Neubig had some code for doing this more efficiently?
        # ToDo: If so we should use his approach instead, otherwise remove the ToDo
        api_key_idx = self.__last_call_per_key.index(min(self.__last_call_per_key))
        last_call_on_key = time.time() - self.__last_call_per_key[api_key_idx]
        good_to_go = last_call_on_key > self.__waittime_per_key

        if not good_to_go:
            time.sleep(self.__waittime_per_key - last_call_on_key)
            return self._choose_next_api_key()

        self.__last_call_per_key[api_key_idx] = time.time()
        return api_key_idx
    
    def _call(self,**kwargs) -> List[str]:
        merged_params = {**self.params,**kwargs}

        #IF n > 1 for streams, the index determines which sentence it's completing
        #           for standard messae, 
        # list in choices but index still indicates which sentence we're talking about
        response = completion(**merged_params)
        
        if merged_params.get("stream", None):
            messages = merge_streams(response,n_chat_completion_choices=kwargs.get("n",1))
        else:
            messages = [choice["message"] for choice in response["choices"]]
        return messages
    
    def _get_model_and_api_dict(self,api_key_info):
        api_backend = api_key_info.backend_used
        api_base = api_key_info.api_base
        api_key = api_key_info.api_key
        api_version = api_key_info.api_version
        
        #deals with model_name type. You can pass either a single model (usually whey you're using a single API)
        # Or a dictionary from API to model (e.g. {"azure": "azure/gpt-4", {"openai": "gpt-4"}})
        #The model names follow the naming of the litellm library
        if isinstance(self.model_name,dict):
            assert api_backend in  self.model_name.keys() , \
            f"A model has not been specified for the backend '{api_backend}'.Currently specified backend to model mappings: { self.model_name}"
            model_name =  self.model_name[api_backend]
        else:
            model_name =  self.model_name
        
        litellm_api_info = {"model": model_name, "api_base": api_base, "api_version": api_version , "api_key": api_key }
        
        return litellm_api_info
            
    def __call__(self,**kwargs):
        api_key_idx = self._choose_next_api_key()
        api_key_info = self.api_infos[api_key_idx]
        
        litellm_api_info = self._get_model_and_api_dict(api_key_info)
        
        merged_kwargs = {**kwargs,**litellm_api_info}
        
        return self._call(**merged_kwargs)
        
    
        
        
        
        