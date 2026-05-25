from pydantic import BaseModel


class PlanOut(BaseModel):
    slug: str
    title: str
    price_usd: float
    cpu: str
    ram: str
    storage: str
    bandwidth: str
    vcpu: int
    ram_gb: int
    storage_gb: int
    product_id: str
    provider: str
    badge: str | None = None
