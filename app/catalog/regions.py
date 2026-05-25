"""Display regions for CloudBox UI — mapped to Contabo provider codes."""

from app.schemas.regions import RegionOut

DISPLAY_REGIONS: list[RegionOut] = [
    RegionOut(
        id="kigali",
        label="Kigali",
        country="Rwanda",
        flag="🇷🇼",
        latency_ms=6,
        provider_code="EU",
    ),
    RegionOut(
        id="nairobi",
        label="Nairobi",
        country="Kenya",
        flag="🇰🇪",
        latency_ms=18,
        provider_code="EU",
    ),
    RegionOut(
        id="johannesburg",
        label="Johannesburg",
        country="South Africa",
        flag="🇿🇦",
        latency_ms=24,
        provider_code="EU",
    ),
    RegionOut(
        id="frankfurt",
        label="Frankfurt",
        country="Germany",
        flag="🇩🇪",
        latency_ms=68,
        provider_code="EU",
    ),
    RegionOut(
        id="london",
        label="London",
        country="United Kingdom",
        flag="🇬🇧",
        latency_ms=72,
        provider_code="UK",
    ),
    RegionOut(
        id="singapore",
        label="Singapore",
        country="Singapore",
        flag="🇸🇬",
        latency_ms=95,
        provider_code="SIN",
    ),
    RegionOut(
        id="us-east",
        label="New York",
        country="United States",
        flag="🇺🇸",
        latency_ms=110,
        provider_code="US-east",
    ),
]

REGION_ALIASES: dict[str, str] = {
    "kigali": "EU",
    "nairobi": "EU",
    "johannesburg": "EU",
    "frankfurt": "EU",
}


def resolve_region_code(region: str) -> str:
    key = region.strip().lower().replace(" ", "-")
    if key in REGION_ALIASES:
        return REGION_ALIASES[key]
    for r in DISPLAY_REGIONS:
        if r.id == key or r.provider_code.upper() == region.upper():
            return r.provider_code
    return region.upper() if len(region) <= 12 else region
