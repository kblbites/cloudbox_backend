from abc import ABC, abstractmethod
from typing import Any

from app.schemas.common import PaginatedResponse
from app.schemas.images import ImageOut
from app.schemas.regions import RegionOut
from app.schemas.servers import (
    ServerAction,
    ServerCreate,
    ServerOut,
    ServerStatus,
)


class CloudProvider(ABC):
    """Abstract interface for VPS cloud providers."""

    name: str

    @abstractmethod
    async def list_servers(
        self,
        *,
        page: int = 1,
        size: int = 25,
        status: ServerStatus | None = None,
        search: str | None = None,
    ) -> PaginatedResponse[ServerOut]:
        ...

    @abstractmethod
    async def get_server(self, server_id: str) -> ServerOut:
        ...

    @abstractmethod
    async def create_server(self, payload: ServerCreate) -> ServerOut:
        ...

    @abstractmethod
    async def delete_server(self, server_id: str) -> None:
        ...

    @abstractmethod
    async def server_action(self, server_id: str, action: ServerAction) -> ServerOut:
        ...

    @abstractmethod
    async def list_regions(self) -> list[RegionOut]:
        ...

    @abstractmethod
    async def list_images(
        self,
        *,
        search: str | None = None,
        standard_image: bool | None = None,
    ) -> list[ImageOut]:
        ...

    @abstractmethod
    async def health_check(self) -> dict[str, Any]:
        ...
