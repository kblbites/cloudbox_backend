import uuid
from typing import Any

import httpx

from fastapi import status

from app.config import Settings
from app.core.exceptions import ProviderAPIError


class ContaboClient:
    """Low-level HTTP client for Contabo API + OAuth2 token management."""

    def __init__(self, settings: Settings):
        self._settings = settings
        self._access_token: str | None = None

    def _headers(self, *, trace_id: str | None = None) -> dict[str, str]:
        if not self._access_token:
            raise ProviderAPIError("contabo", "Not authenticated — missing access token")
        headers = {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json",
            "x-request-id": str(uuid.uuid4()),
        }
        if trace_id:
            headers["x-trace-id"] = trace_id
        return headers

    def _auth_error_message(self, response: httpx.Response) -> str:
        try:
            body = response.json()
            error = body.get("error", "")
            desc = body.get("error_description", "")
            if error == "invalid_grant":
                return (
                    "Invalid Contabo API User or API Password. "
                    "In my.contabo.com → Account → API, use the API User email and the "
                    "API Password created on that page (not your normal login password). "
                    "Reset the API password if unsure, then update backend/.env and restart the server."
                )
            if desc:
                return f"Contabo authentication failed: {desc}"
        except Exception:
            pass
        return f"Contabo authentication failed: {response.text}"

    async def authenticate(self) -> None:
        data = {
            "client_id": self._settings.contabo_client_id,
            "client_secret": self._settings.contabo_client_secret,
            "username": self._settings.contabo_api_user,
            "password": self._settings.contabo_api_password,
            "grant_type": "password",
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(self._settings.contabo_auth_url, data=data)
        if response.status_code >= 400:
            message = self._auth_error_message(response)
            raise ProviderAPIError(
                "contabo",
                message,
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        payload = response.json()
        token = payload.get("access_token")
        if not token:
            raise ProviderAPIError("contabo", "Authentication response missing access_token")
        self._access_token = token

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        if not self._access_token:
            await self.authenticate()

        url = f"{self._settings.contabo_api_base_url.rstrip('/')}{path}"
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.request(
                method,
                url,
                headers=self._headers(trace_id=trace_id),
                params=params,
                json=json,
            )

        if response.status_code == 401:
            await self.authenticate()
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.request(
                    method,
                    url,
                    headers=self._headers(trace_id=trace_id),
                    params=params,
                    json=json,
                )

        if response.status_code >= 400:
            code = (
                status.HTTP_503_SERVICE_UNAVAILABLE
                if response.status_code in (401, 403)
                else status.HTTP_502_BAD_GATEWAY
            )
            raise ProviderAPIError(
                "contabo",
                f"{method} {path} failed ({response.status_code}): {response.text}",
                status_code=code,
            )

        if response.status_code == 204 or not response.content:
            return {}
        return response.json()

    async def list_instances(
        self,
        *,
        page: int = 1,
        size: int = 25,
        status: str | None = None,
        search: str | None = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {"page": page, "size": size}
        if status:
            params["status"] = status
        if search:
            params["search"] = search
        return await self._request("GET", "/v1/compute/instances", params=params)

    async def get_instance(self, instance_id: int) -> dict[str, Any]:
        return await self._request("GET", f"/v1/compute/instances/{instance_id}")

    async def create_instance(self, body: dict[str, Any]) -> dict[str, Any]:
        return await self._request("POST", "/v1/compute/instances", json=body)

    async def cancel_instance(self, instance_id: int) -> dict[str, Any]:
        return await self._request("POST", f"/v1/compute/instances/{instance_id}/cancel")

    async def instance_action(self, instance_id: int, action: str) -> dict[str, Any]:
        return await self._request(
            "POST",
            f"/v1/compute/instances/{instance_id}/actions/{action}",
        )

    async def list_images(
        self,
        *,
        page: int = 1,
        size: int = 100,
        search: str | None = None,
        standard_image: bool | None = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {"page": page, "size": size}
        if search:
            params["search"] = search
        if standard_image is not None:
            params["standardImage"] = str(standard_image).lower()
        return await self._request("GET", "/v1/compute/images", params=params)

    async def list_all_images(
        self,
        *,
        search: str | None = None,
        standard_image: bool | None = None,
        page_size: int = 100,
    ) -> list[dict[str, Any]]:
        """Fetch every page of images from Contabo."""
        all_items: list[dict[str, Any]] = []
        page = 1
        total_pages = 1
        while page <= total_pages:
            raw = await self.list_images(
                page=page,
                size=page_size,
                search=search,
                standard_image=standard_image,
            )
            all_items.extend(raw.get("data") or [])
            pagination = raw.get("_pagination") or {}
            total_pages = int(pagination.get("totalPages") or 1)
            page += 1
        return all_items

    async def list_secrets(self) -> dict[str, Any]:
        return await self._request("GET", "/v1/secrets")

    async def create_secret(self, body: dict[str, Any]) -> dict[str, Any]:
        return await self._request("POST", "/v1/secrets", json=body)
