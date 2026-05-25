from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.db.models import User
from app.dependencies import get_provisioning_service
from app.catalog.plans import RAM_OPTIONS, STORAGE_OPTIONS, VCPU_OPTIONS
from app.schemas.plans import PlanOut
from app.schemas.secrets import PlanOptionsOut
from app.services.provisioning import ProvisioningService

router = APIRouter()


@router.get("", response_model=list[PlanOut])
def list_plans(
    _current_user: User = Depends(get_current_user),
    service: ProvisioningService = Depends(get_provisioning_service),
) -> list[PlanOut]:
    return service.list_plans()


@router.get("/options", response_model=PlanOptionsOut)
def plan_options(_current_user: User = Depends(get_current_user)) -> PlanOptionsOut:
    return PlanOptionsOut(
        vcpu_options=VCPU_OPTIONS,
        ram_options=RAM_OPTIONS,
        storage_options=STORAGE_OPTIONS,
    )
