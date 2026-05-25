from pydantic import BaseModel


class ProviderInfo(BaseModel):
    name: str
    display_name: str
    configured: bool
    implemented: bool
    is_default: bool
