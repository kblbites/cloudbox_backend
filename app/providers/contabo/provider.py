from typing import Any

from app.catalog.plans import plan_to_product_id
from app.catalog.regions import DISPLAY_REGIONS, resolve_region_code
from app.config import Settings
from app.core.exceptions import CloudBoxError, ProviderNotConfiguredError
from fastapi import status
from app.providers.base import CloudProvider
from app.providers.contabo.client import ContaboClient
from app.providers.contabo.mappers import image_to_out, instance_to_server
from app.schemas.common import PaginatedResponse
from app.schemas.images import ImageOut
from app.schemas.regions import RegionOut
from app.schemas.servers import (
    ServerAction,
    ServerCreate,
    ServerOut,
    ServerStatus,
)


DEFAULT_UBUNTU_IMAGE = "afecbb85-e2fc-46f0-9684-b46b1faf00bb"

ACTION_PATHS: dict[ServerAction, str] = {
    ServerAction.START: "start",
    ServerAction.STOP: "stop",
    ServerAction.RESTART: "restart",
    ServerAction.SHUTDOWN: "shutdown",
}


class ContaboProvider(CloudProvider):
    name = "contabo"

    def __init__(self, settings: Settings):
        if not settings.contabo_configured():
            raise ProviderNotConfiguredError(self.name)
        self._client = ContaboClient(settings)

    async def list_servers(
        self,
        *,
        page: int = 1,
        size: int = 25,
        status: ServerStatus | None = None,
        search: str | None = None,
    ) -> PaginatedResponse[ServerOut]:
        raw = await self._client.list_instances(
            page=page,
            size=size,
            status=status.value if status else None,
            search=search,
        )
        data = raw.get("data") or []
        pagination = raw.get("_pagination") or {}
        items = [instance_to_server(i) for i in data]
        return PaginatedResponse(
            items=items,
            page=pagination.get("page", page),
            size=pagination.get("size", size),
            total=pagination.get("totalElements"),
        )

    async def get_server(self, server_id: str) -> ServerOut:
        raw = await self._client.get_instance(int(server_id))
        data = raw.get("data") or []
        if not data:
            from app.core.exceptions import ProviderAPIError

            raise ProviderAPIError("contabo", f"Instance {server_id} not found", status_code=404)
        return instance_to_server(data[0])

    async def _secret_id_from_response(self, raw: dict[str, Any]) -> int:
        data = raw.get("data") or []
        if not data:
            raise CloudBoxError("contabo", "Secret creation returned empty data", status_code=502)
        return int(data[0].get("secretId") or data[0].get("secret_id"))

    async def _create_password_secret(self, name: str, password: str) -> int:
        raw = await self._client.create_secret(
            {"name": name, "value": password, "type": "password"},
        )
        return await self._secret_id_from_response(raw)

    async def _create_ssh_secret(self, name: str, public_key: str) -> int:
        raw = await self._client.create_secret(
            {"name": name, "value": public_key.strip(), "type": "ssh"},
        )
        return await self._secret_id_from_response(raw)

    async def list_secrets(self) -> list[dict[str, Any]]:
        try:
            raw = await self._client.list_secrets()
            return raw.get("data") or []
        except Exception:
            return []

    async def create_server(self, payload: ServerCreate) -> ServerOut:
        product_id = plan_to_product_id(payload.plan_slug, self.name)
        region_key = payload.region_id or payload.region
        region = resolve_region_code(region_key)

        ssh_ids = list(payload.ssh_key_ids)
        if payload.ssh_public_key:
            ssh_ids.append(
                await self._create_ssh_secret(
                    f"cloudbox-{payload.display_name}-ssh",
                    payload.ssh_public_key,
                )
            )

        root_secret_id = payload.root_password_secret_id
        if payload.root_password:
            root_secret_id = await self._create_password_secret(
                f"cloudbox-{payload.display_name}-pwd",
                payload.root_password,
            )
        elif payload.auth_method == "password" and root_secret_id is None:
            raise CloudBoxError(
                "Root password is required for password authentication",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        elif payload.auth_method == "ssh_key" and not ssh_ids:
            raise CloudBoxError(
                "SSH public key is required for SSH key authentication",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        body: dict[str, Any] = {
            "productId": product_id,
            "region": region,
            "period": payload.period_months,
            "displayName": payload.display_name,
            "defaultUser": payload.default_user,
            "imageId": payload.image_id or DEFAULT_UBUNTU_IMAGE,
        }
        if ssh_ids:
            body["sshKeys"] = ssh_ids
        if root_secret_id is not None:
            body["rootPassword"] = root_secret_id
        if payload.user_data:
            body["userData"] = payload.user_data

        raw = await self._client.create_instance(body)
        data = raw.get("data") or []
        if not data:
            from app.core.exceptions import ProviderAPIError

            raise ProviderAPIError("contabo", "Create instance returned empty data")
        return instance_to_server(data[0], plan_slug=payload.plan_slug)

    async def delete_server(self, server_id: str) -> None:
        await self._client.cancel_instance(int(server_id))

    async def server_action(self, server_id: str, action: ServerAction) -> ServerOut:
        path_action = ACTION_PATHS[action]
        await self._client.instance_action(int(server_id), path_action)
        return await self.get_server(server_id)

    async def list_regions(self) -> list[RegionOut]:
        return list(DISPLAY_REGIONS)

    async def list_images(
        self,
        *,
        search: str | None = None,
        standard_image: bool | None = None,
    ) -> list[ImageOut]:
        data = await self._client.list_all_images(
            search=search,
            standard_image=standard_image,
        )
        return [image_to_out(i) for i in data]

    async def health_check(self) -> dict[str, Any]:
        await self._client.authenticate()
        return {"provider": self.name, "authenticated": True}
