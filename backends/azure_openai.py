from __future__ import annotations
from pydantic import root_validator

from backends.openai import SafeChatOpenAI



import logging
from typing import Any, Dict, Mapping, Optional


from langchain.schema import ChatResult

logger = logging.getLogger(__name__)


class SafeAzureChatOpenAI(SafeChatOpenAI):
    """Edited version of langchain.chat_models.AzureChatOpenAI to allow for multithread calls
    """


    deployment_name: str = ""
    openai_api_type: str = "azure"
    openai_api_base: str = None
    openai_api_version: Optional[str] = None
    openai_api_key: Optional[str] = None
    openai_organization: Optional[str] = None
    openai_proxy: Optional[str] = None

    # overrides the super class validator
    @root_validator()
    def validate_environment(cls, values: Dict) -> Dict:
        """Validate that api key and python package exists in environment."""
        # TODO: is it safe to read from the environment & the openai.attr?
        #   if not, there are set default values for api_base, etc. see openai\__init__.py
        try:
            import openai

        except ImportError:
            raise ValueError(
                "Could not import openai python package. "
                "Please install it with `pip install openai`."
            )
        openai_api_key = super()._get_from_dict_or_env(
            values,
            "openai_api_key",
            "OPENAI_API_KEY",
            dict_only=False,
        )
        openai_api_base = super()._get_from_dict_or_env(
            values,
            "openai_api_base",
            "OPENAI_API_BASE",
            dict_only=False,
        )
        openai_proxy = super()._get_from_dict_or_env(
            values,
            "openai_proxy",
            "OPENAI_PROXY",
            default="",
            dict_only=False,
        )
        openai_organization = super()._get_from_dict_or_env(
            values,
            "openai_organization",
            "OPENAI_ORGANIZATION",
            default="",
            dict_only=False,
        )
        openai_api_version = super()._get_from_dict_or_env(
            values,
            "openai_api_version",
            "OPENAI_API_VERSION",
            dict_only=False,
        )
        openai_api_type = super()._get_from_dict_or_env(
            values,
            "openai_api_type",
            "OPENAI_API_TYPE",
            default="azure",
            dict_only=False,
        )
        values["openai_api_key"] = openai_api_key
        values["openai_api_base"] = openai_api_base
        values["openai_api_version"] = openai_api_version
        values["openai_api_type"] = openai_api_type
        values["openai_organization"] = openai_organization if openai_organization else None
        values["openai_proxy"] = {"http": openai_proxy, "https": openai_proxy} if openai_proxy else None

        try:
            values["client"] = openai.ChatCompletion
        except AttributeError:
            raise ValueError(
                "`openai` has no `ChatCompletion` attribute, this is likely "
                "due to an old version of the openai package. Try upgrading it "
                "with `pip install --upgrade openai`."
            )
        if values["n"] < 1:
            raise ValueError("n must be at least 1.")
        if values["n"] > 1 and values["streaming"]:
            raise ValueError("n must be 1 when streaming.")
        return values


    @property
    def _default_params(self) -> Dict[str, Any]:
        """Get the default parameters for calling OpenAI API."""
        return {
            **super()._default_params,
            "engine": self.deployment_name,
        }

    @property
    def _identifying_params(self) -> Mapping[str, Any]:
        """Get the identifying parameters."""
        return {**self._default_params}

    @property
    def _llm_type(self) -> str:
        return "azure-openai-chat"

    def _create_chat_result(self, response: Mapping[str, Any]) -> ChatResult:
        for res in response["choices"]:
            if res.get("finish_reason", None) == "content_filter":
                raise ValueError(
                    "Azure has not provided the response due to a content"
                    " filter being triggered"
                )
        return super()._create_chat_result(response)
