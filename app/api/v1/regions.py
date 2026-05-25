from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_user
from app.core.exceptions import CloudBoxError, to_http_exception
from app.db.models import User
from app.dependencies import get_provisioning_service
from app.schemas.regions import RegionOut
from app.services.provisioning import ProvisioningService

router = APIRouter()


@router.get("", response_model=list[RegionOut])
async def list_regions(
    provider: str | None = Query(default=None),
    _current_user: User = Depends(get_current_user),
    service: ProvisioningService = Depends(get_provisioning_service),
) -> list[RegionOut]:
    try:
        return await service.list_regions(provider=provider)
    except CloudBoxError as exc:
        raise to_http_exception(exc) from exc
