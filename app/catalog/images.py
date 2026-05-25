"""Fallback OS images when Contabo API is unavailable."""

from app.schemas.images import ImageOut

# Contabo default image IDs (see https://api.contabo.com/)
DEFAULT_IMAGES: list[ImageOut] = [
    ImageOut(
        id="afecbb85-e2fc-46f0-9684-b46b1faf00bb",
        name="Ubuntu 22.04",
        description="Default Ubuntu LTS",
        os_type="Linux",
        standard_image=True,
        provider="contabo",
    ),
    ImageOut(
        id="3f184ab8-a600-4e7c-8c9b-3413e21a3752",
        name="Ubuntu 24.04",
        description="Ubuntu LTS",
        os_type="Linux",
        standard_image=True,
        provider="contabo",
    ),
]
