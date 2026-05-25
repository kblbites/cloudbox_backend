from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    page: int = 1
    size: int = 25
    total: int | None = None


class HealthResponse(BaseModel):
    status: str = "ok"
    app: str
    environment: str
    default_provider: str
    providers: dict[str, str]
