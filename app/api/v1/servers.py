from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.exceptions import CloudBoxError, to_http_exception
from app.db.database import get_db
from app.db.models import User
from app.dependencies import get_provisioning_service
from app.schemas.common import PaginatedResponse
from app.schemas.servers import ServerAction, ServerCreate, ServerOut
from app.services.provisioning import ProvisioningService

router = APIRouter()


@router.get("", response_model=PaginatedResponse[ServerOut])
async def list_servers(
    provider: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=25, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: ProvisioningService = Depends(get_provisioning_service),
) -> PaginatedResponse[ServerOut]:
    try:
        return await service.list_servers(
            db, current_user, provider=provider, page=page, size=size
        )
    except CloudBoxError as exc:
        raise to_http_exception(exc) from exc


@router.get("/{server_id}", response_model=ServerOut)
async def get_server(
    server_id: str,
    provider: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: ProvisioningService = Depends(get_provisioning_service),
) -> ServerOut:
    try:
        return await service.get_server(
            db, current_user, server_id, provider=provider
        )
    except CloudBoxError as exc:
        raise to_http_exception(exc) from exc


@router.post("", response_model=ServerOut, status_code=201)
async def create_server(
    payload: ServerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: ProvisioningService = Depends(get_provisioning_service),
) -> ServerOut:
    try:
        return await service.create_server(db, current_user, payload)
    except CloudBoxError as exc:
        raise to_http_exception(exc) from exc
    except ValueError as exc:
        raise to_http_exception(CloudBoxError(str(exc), status_code=400)) from exc


@router.delete("/{server_id}", status_code=204)
async def delete_server(
    server_id: str,
    provider: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: ProvisioningService = Depends(get_provisioning_service),
) -> None:
    try:
        await service.delete_server(
            db, current_user, server_id, provider=provider
        )
    except CloudBoxError as exc:
        raise to_http_exception(exc) from exc


@router.post("/{server_id}/actions/{action}", response_model=ServerOut)
async def server_action(
    server_id: str,
    action: ServerAction,
    provider: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: ProvisioningService = Depends(get_provisioning_service),
) -> ServerOut:
    try:
        return await service.server_action(
            db, current_user, server_id, action, provider=provider
        )
    except CloudBoxError as exc:
        raise to_http_exception(exc) from exc
