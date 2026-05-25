import httpx
from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.config import get_settings
from app.db.models import User
from app.dependencies import get_registry
from app.providers.registry import ProviderRegistry
from app.schemas.providers import ProviderInfo

router = APIRouter()


async def _test_contabo_token() -> tuple[bool, str | None]:
    settings = get_settings()
    if not settings.contabo_configured():
        return False, "Contabo credentials missing in .env"
    data = {
        "client_id": settings.contabo_client_id,
        "client_secret": settings.contabo_client_secret,
        "username": settings.contabo_api_user,
        "password": settings.contabo_api_password,
        "grant_type": "password",
    }
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(settings.contabo_auth_url, data=data)
        if response.status_code == 200 and response.json().get("access_token"):
            return True, None
        if response.status_code == 401:
            return False, (
                "Invalid API User or API Password. Reset the API password at "
                "https://my.contabo.com/account/api and update backend/.env"
            )
        return False, f"Contabo auth failed ({response.status_code})"
    except httpx.HTTPError as exc:
        return False, str(exc)


@router.get("", response_model=list[ProviderInfo])
def list_providers(
    _current_user: User = Depends(get_current_user),
    registry: ProviderRegistry = Depends(get_registry),
) -> list[ProviderInfo]:
    return [ProviderInfo(**p) for p in registry.list_providers()]


@router.get("/contabo/status")
async def contabo_status(
    _current_user: User = Depends(get_current_user),
) -> dict:
    ok, error = await _test_contabo_token()
    settings = get_settings()
    return {
        "provider": "contabo",
        "connected": ok,
        "configured": settings.contabo_configured(),
        "api_user": settings.contabo_api_user,
        "error": error,
    }
