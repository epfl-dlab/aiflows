from dataclasses import dataclass
from typing import Optional
from aiflows.utils import logging
logger = logging.get_logger(__name__)
logger.warn = logger.warning
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
    
    def __post_init__(self):
        self.validate()

    def validate(self):
        if self.backend_used is None:
            logger.warn("backend_used is set to None")
            
        if self.api_key is None:
            logger.warn(" Your api_key is set to None. If this is not intended, "
                        "please set it to a valid key (Note: if you've loaded your key from an environment variable, "
                        "consider checking if the environment variable is set correctly "
                        "and reactivating the environment variable.)")
        
