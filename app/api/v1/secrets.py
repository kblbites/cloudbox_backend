from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_user
from app.core.exceptions import CloudBoxError, to_http_exception
from app.db.models import User
from app.dependencies import get_provisioning_service
from app.schemas.secrets import SecretCreatePassword, SecretCreateSsh, SecretOut
from app.services.provisioning import ProvisioningService

router = APIRouter()


@router.get("", response_model=list[SecretOut])
async def list_secrets(
    provider: str | None = Query(default=None),
    _current_user: User = Depends(get_current_user),
    service: ProvisioningService = Depends(get_provisioning_service),
) -> list[SecretOut]:
    try:
        return await service.list_secrets(provider=provider)
    except CloudBoxError as exc:
        raise to_http_exception(exc) from exc


@router.post("/password", response_model=SecretOut, status_code=201)
async def create_password_secret(
    payload: SecretCreatePassword,
    provider: str | None = Query(default=None),
    _current_user: User = Depends(get_current_user),
    service: ProvisioningService = Depends(get_provisioning_service),
) -> SecretOut:
    try:
        return await service.create_password_secret(
            payload.name, payload.password, provider=provider
        )
    except CloudBoxError as exc:
        raise to_http_exception(exc) from exc


@router.post("/ssh", response_model=SecretOut, status_code=201)
async def create_ssh_secret(
    payload: SecretCreateSsh,
    provider: str | None = Query(default=None),
    _current_user: User = Depends(get_current_user),
    service: ProvisioningService = Depends(get_provisioning_service),
) -> SecretOut:
    try:
        return await service.create_ssh_secret(
            payload.name, payload.public_key, provider=provider
        )
    except CloudBoxError as exc:
        raise to_http_exception(exc) from exc
