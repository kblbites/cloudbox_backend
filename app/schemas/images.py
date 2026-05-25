from pydantic import BaseModel


class ImageOut(BaseModel):
    id: str
    name: str | None = None
    description: str | None = None
    os_type: str | None = None
    version: str | None = None
    format: str | None = None
    status: str | None = None
    standard_image: bool | None = None
    size_mb: int | None = None
    provider: str
