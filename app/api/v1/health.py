from fastapi import APIRouter, Depends

from app.config import Settings
from app.dependencies import get_app_settings, get_registry
from app.providers.registry import ProviderRegistry
from app.schemas.common import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health(
    settings: Settings = Depends(get_app_settings),
    registry: ProviderRegistry = Depends(get_registry),
) -> HealthResponse:
    providers_status = {
        p["name"]: "ready" if p["configured"] and p["implemented"] else "not_configured"
        for p in registry.list_providers()
    }
    return HealthResponse(
        status="ok",
        app=settings.app_name,
        environment=settings.app_env,
        default_provider=settings.default_provider,
        providers=providers_status,
    )
