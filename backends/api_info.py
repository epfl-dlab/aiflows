from dataclasses import dataclass
from typing import Optional


@dataclass
class ApiInfo:
    backend_used: str = None
    api_version: Optional[str] = None
    api_key: str = None
    api_base: Optional[str] = None
