from app.config import Settings, get_settings
from app.providers.registry import ProviderRegistry, get_provider_registry
from app.services.provisioning import ProvisioningService


def get_provisioning_service() -> ProvisioningService:
    return ProvisioningService(get_provider_registry())


def get_registry() -> ProviderRegistry:
    return get_provider_registry()


def get_app_settings() -> Settings:
    return get_settings()
