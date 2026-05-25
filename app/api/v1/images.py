from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_user
from app.core.exceptions import CloudBoxError, to_http_exception
from app.db.models import User
from app.dependencies import get_provisioning_service
from app.schemas.images import ImageOut
from app.services.provisioning import ProvisioningService

router = APIRouter()


@router.get("", response_model=list[ImageOut])
async def list_images(
    provider: str | None = Query(default=None),
    search: str | None = Query(default=None),
    standard_image: bool | None = Query(default=None),
    fallback: bool = Query(
        default=False,
        description="If true, return default Ubuntu images when provider is unavailable",
    ),
    _current_user: User = Depends(get_current_user),
    service: ProvisioningService = Depends(get_provisioning_service),
) -> list[ImageOut]:
    try:
        return await service.list_images(
            provider=provider,
            search=search,
            standard_image=standard_image,
            fallback=fallback,
        )
    except CloudBoxError as exc:
        raise to_http_exception(exc) from exc
