from sqlalchemy.orm import Session

from app.catalog.images import DEFAULT_IMAGES
from app.catalog.plans import CLOUDBOX_PLANS
from app.config import get_settings
from app.core.exceptions import ProviderAPIError
from app.db.models import ServerRecord, User
from app.providers.registry import ProviderRegistry
from app.schemas.common import PaginatedResponse
from app.schemas.images import ImageOut
from app.schemas.plans import PlanOut
from app.schemas.regions import RegionOut
from app.schemas.secrets import SecretOut
from app.schemas.servers import ServerAction, ServerCreate, ServerOut, ServerStatus


def _parse_status(raw: str) -> ServerStatus:
    try:
        return ServerStatus(raw)
    except ValueError:
        return ServerStatus.UNKNOWN


class ProvisioningService:
    """Orchestrates VM lifecycle across provider adapters."""

    def __init__(self, registry: ProviderRegistry):
        self._registry = registry

    def _provider(self, name: str | None = None):
        return self._registry.get(name)

    def _record_to_out(self, record: ServerRecord) -> ServerOut:
        return ServerOut(
            id=record.external_id,
            display_name=record.display_name,
            status=_parse_status(record.status),
            region=record.region,
            provider=record.provider,
            image_id=record.image_id,
            ipv4=record.ipv4,
            plan_slug=record.plan_slug,
            created_at=record.created_at.isoformat() if record.created_at else None,
        )

    async def _sync_record(self, db: Session, record: ServerRecord) -> ServerOut:
        try:
            live = await self._provider(record.provider).get_server(record.external_id)
            record.status = live.status.value
            if live.ipv4:
                record.ipv4 = live.ipv4
            db.commit()
            db.refresh(record)
        except Exception:
            pass
        return self._record_to_out(record)

    async def list_servers(
        self,
        db: Session,
        user: User,
        *,
        provider: str | None = None,
        page: int = 1,
        size: int = 25,
    ) -> PaginatedResponse[ServerOut]:
        query = db.query(ServerRecord).filter(ServerRecord.user_id == user.id)
        if provider:
            query = query.filter(ServerRecord.provider == provider)
        total = query.count()
        records = (
            query.order_by(ServerRecord.created_at.desc())
            .offset((page - 1) * size)
            .limit(size)
            .all()
        )
        items: list[ServerOut] = []
        for record in records:
            items.append(await self._sync_record(db, record))
        return PaginatedResponse(items=items, page=page, size=size, total=total)

    async def get_server(
        self,
        db: Session,
        user: User,
        server_id: str,
        *,
        provider: str | None = None,
    ) -> ServerOut:
        record = (
            db.query(ServerRecord)
            .filter(
                ServerRecord.user_id == user.id,
                ServerRecord.external_id == server_id,
            )
            .first()
        )
        if not record:
            from app.core.exceptions import CloudBoxError
            from fastapi import status

            raise CloudBoxError("Server not found", status_code=status.HTTP_404_NOT_FOUND)
        if provider and record.provider != provider:
            from app.core.exceptions import CloudBoxError
            from fastapi import status

            raise CloudBoxError("Server not found", status_code=status.HTTP_404_NOT_FOUND)
        return await self._sync_record(db, record)

    async def create_server(self, db: Session, user: User, payload: ServerCreate) -> ServerOut:
        provider_name = payload.provider or get_settings().default_provider
        created = await self._provider(payload.provider).create_server(payload)
        record = ServerRecord(
            user_id=user.id,
            external_id=created.id,
            provider=provider_name,
            display_name=payload.display_name,
            plan_slug=payload.plan_slug,
            region=payload.region,
            image_id=payload.image_id or created.image_id,
            status=created.status.value,
            ipv4=created.ipv4,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return self._record_to_out(record)

    async def delete_server(
        self,
        db: Session,
        user: User,
        server_id: str,
        *,
        provider: str | None = None,
    ) -> None:
        record = (
            db.query(ServerRecord)
            .filter(
                ServerRecord.user_id == user.id,
                ServerRecord.external_id == server_id,
            )
            .first()
        )
        if not record:
            from app.core.exceptions import CloudBoxError
            from fastapi import status

            raise CloudBoxError("Server not found", status_code=status.HTTP_404_NOT_FOUND)
        await self._provider(record.provider).delete_server(server_id)
        db.delete(record)
        db.commit()

    async def server_action(
        self,
        db: Session,
        user: User,
        server_id: str,
        action: ServerAction,
        *,
        provider: str | None = None,
    ) -> ServerOut:
        record = (
            db.query(ServerRecord)
            .filter(
                ServerRecord.user_id == user.id,
                ServerRecord.external_id == server_id,
            )
            .first()
        )
        if not record:
            from app.core.exceptions import CloudBoxError
            from fastapi import status

            raise CloudBoxError("Server not found", status_code=status.HTTP_404_NOT_FOUND)
        await self._provider(record.provider).server_action(server_id, action)
        return await self._sync_record(db, record)

    async def list_regions(self, *, provider: str | None = None) -> list[RegionOut]:
        return await self._provider(provider).list_regions()

    async def list_images(
        self,
        *,
        provider: str | None = None,
        search: str | None = None,
        standard_image: bool | None = None,
        fallback: bool = False,
    ) -> list[ImageOut]:
        try:
            return await self._provider(provider).list_images(
                search=search,
                standard_image=standard_image,
            )
        except ProviderAPIError:
            if fallback:
                return list(DEFAULT_IMAGES)
            raise

    def list_plans(self) -> list[PlanOut]:
        return list(CLOUDBOX_PLANS.values())

    async def list_secrets(self, *, provider: str | None = None) -> list[SecretOut]:
        try:
            p = self._provider(provider)
            if hasattr(p, "list_secrets"):
                raw = await p.list_secrets()
                return [
                    SecretOut(
                        id=int(item.get("secretId") or item.get("secret_id")),
                        name=item.get("name", ""),
                        type=item.get("type", ""),
                    )
                    for item in raw
                    if item.get("type") == "ssh"
                ]
        except ProviderAPIError:
            pass
        return []

    async def create_password_secret(
        self, name: str, password: str, *, provider: str | None = None
    ) -> SecretOut:
        p = self._provider(provider)
        secret_id = await p._create_password_secret(name, password)
        return SecretOut(id=secret_id, name=name, type="password")

    async def create_ssh_secret(
        self, name: str, public_key: str, *, provider: str | None = None
    ) -> SecretOut:
        p = self._provider(provider)
        secret_id = await p._create_ssh_secret(name, public_key)
        return SecretOut(id=secret_id, name=name, type="ssh")
