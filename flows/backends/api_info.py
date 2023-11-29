from dataclasses import dataclass
from typing import Optional


@dataclass
class ApiInfo:
    """This class contains the information about an API key.

    :param backend_used: The backend used
    :type backend_used: str, optional
    :param api_version: The version of the API
    :type api_version: str, optional
    :param api_key: The API key
    :type api_key: str, optional
    :param api_base: The base URL of the API
    :type api_base: str, optional
    """

    backend_used: str = None
    api_version: Optional[str] = None
    api_key: str = None
    api_base: Optional[str] = None
