from dataclasses import dataclass
from typing import Optional


@dataclass
class ApiInfo:
    backend_used: str = None
    api_key: str = None
    endpoint: Optional[str] = None
