"""CloudBox plan catalog — maps UI plans to provider product IDs."""

from app.schemas.plans import PlanOut

CONTABO_PLANS: dict[str, PlanOut] = {
    "basic": PlanOut(
        slug="basic",
        title="Basic",
        price_usd=10.0,
        cpu="2 vCPU",
        ram="4 GB RAM",
        storage="80 GB NVMe SSD",
        bandwidth="2 TB Bandwidth",
        vcpu=2,
        ram_gb=4,
        storage_gb=80,
        product_id="V94",
        provider="contabo",
        badge="Popular",
    ),
    "standard": PlanOut(
        slug="standard",
        title="Standard",
        price_usd=20.0,
        cpu="4 vCPU",
        ram="8 GB RAM",
        storage="160 GB NVMe SSD",
        bandwidth="3 TB Bandwidth",
        vcpu=4,
        ram_gb=8,
        storage_gb=160,
        product_id="V97",
        provider="contabo",
    ),
    "premium": PlanOut(
        slug="premium",
        title="Premium",
        price_usd=40.0,
        cpu="8 vCPU",
        ram="16 GB RAM",
        storage="320 GB NVMe SSD",
        bandwidth="4 TB Bandwidth",
        vcpu=8,
        ram_gb=16,
        storage_gb=320,
        product_id="V100",
        provider="contabo",
    ),
    "business": PlanOut(
        slug="business",
        title="Business",
        price_usd=80.0,
        cpu="16 vCPU",
        ram="32 GB RAM",
        storage="640 GB NVMe SSD",
        bandwidth="5 TB Bandwidth",
        vcpu=16,
        ram_gb=32,
        storage_gb=640,
        product_id="V103",
        provider="contabo",
    ),
}

CLOUDBOX_PLANS = CONTABO_PLANS

VCPU_OPTIONS = [2, 4, 8, 16]
RAM_OPTIONS = [4, 8, 16, 32]
STORAGE_OPTIONS = [80, 160, 320, 640]


def get_plan_by_slug(slug: str) -> PlanOut | None:
    return CLOUDBOX_PLANS.get(slug)


def plan_to_product_id(slug: str, provider: str = "contabo") -> str:
    plan = get_plan_by_slug(slug)
    if not plan:
        raise ValueError(f"Unknown plan slug: {slug}")
    if plan.provider != provider:
        raise ValueError(f"Plan {slug} is not available for provider {provider}")
    return plan.product_id


def match_plan_slug(vcpu: int, ram_gb: int, storage_gb: int) -> str:
    for slug, plan in CLOUDBOX_PLANS.items():
        if plan.vcpu == vcpu and plan.ram_gb == ram_gb and plan.storage_gb == storage_gb:
            return slug
    return "basic"
