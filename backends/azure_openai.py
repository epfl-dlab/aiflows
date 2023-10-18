from backends.openai import SafeChatOpenAI

from __future__ import annotations

import logging
from typing import Any, Dict, Mapping, Optional


from langchain.schema import ChatResult

logger = logging.getLogger(__name__)


class SafeAzureChatOpenAI(SafeChatOpenAI):
    """Edited version of langchain.chat_models.AzureChatOpenAI to allow for multithread calls
    """

    deployment_name: str = ""
    openai_api_type: str = "azure"
    openai_api_base: Optional[str] = None
    openai_api_version: Optional[str] = None
    openai_api_key: Optional[str] = None
    openai_organization: Optional[str] = None
    openai_proxy: Optional[str] = None


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
