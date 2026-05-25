from app.config import ProviderName, get_settings
from app.core.exceptions import ProviderNotConfiguredError, ProviderNotImplementedError
from app.providers.base import CloudProvider
from app.providers.contabo import ContaboProvider


IMPLEMENTED: dict[ProviderName, type[CloudProvider]] = {
    "contabo": ContaboProvider,
}


class ProviderRegistry:
    """Factory for cloud provider adapters."""

    def list_providers(self) -> list[dict]:
        settings = get_settings()
        result = []
        for name in ("contabo", "digitalocean", "aws"):
            configured = self._is_configured(name, settings)
            implemented = name in IMPLEMENTED
            result.append(
                {
                    "name": name,
                    "display_name": name.replace("_", " ").title(),
                    "configured": configured,
                    "implemented": implemented,
                    "is_default": name == settings.default_provider,
                }
            )
        return result

    def _is_configured(self, name: str, settings) -> bool:
        if name == "contabo":
            return settings.contabo_configured()
        return False

    def get(self, name: str | None = None) -> CloudProvider:
        settings = get_settings()
        provider_name: ProviderName = (name or settings.default_provider)  # type: ignore[assignment]
        if provider_name not in IMPLEMENTED:
            raise ProviderNotImplementedError(provider_name)
        if not self._is_configured(provider_name, settings):
            raise ProviderNotConfiguredError(provider_name)
        return IMPLEMENTED[provider_name](settings)


def get_provider_registry() -> ProviderRegistry:
    return ProviderRegistry()
