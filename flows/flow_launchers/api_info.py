from dataclasses import dataclass


@dataclass
class ApiInfo:
    backend_used: str = None
    api_key: str = None
    endpoint: str = None
