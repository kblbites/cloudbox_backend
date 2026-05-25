from pydantic import BaseModel


class RegionOut(BaseModel):
    """Display region shown in UI; maps to a provider region code."""

    id: str
    label: str
    country: str | None = None
    flag: str = "🌍"
    latency_ms: int | None = None
    provider_code: str
    provider: str = "contabo"
    available: bool = True
