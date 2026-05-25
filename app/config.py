from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


ProviderName = Literal["contabo", "digitalocean", "aws"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "CloudBox API"
    app_env: str = "development"
    debug: bool = True
    api_prefix: str = "/api/v1"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    default_provider: ProviderName = "contabo"

    database_url: str = "sqlite:///./cloudbox.db"
    jwt_secret: str = "change-me-in-production-use-long-random-string"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7  # 7 days

    contabo_client_id: str = ""
    contabo_client_secret: str = ""
    contabo_api_user: str = ""
    contabo_api_password: str = ""
    contabo_api_base_url: str = "https://api.contabo.com"
    contabo_auth_url: str = (
        "https://auth.contabo.com/auth/realms/contabo/protocol/openid-connect/token"
    )

    @field_validator(
        "contabo_client_id",
        "contabo_client_secret",
        "contabo_api_user",
        "contabo_api_password",
        mode="before",
    )
    @classmethod
    def strip_contabo_credentials(cls, v: object) -> object:
        if isinstance(v, str):
            cleaned = v.strip().strip('"').strip("'")
            # Remove zero-width / BOM characters from copy-paste
            return "".join(c for c in cleaned if c.isprintable() or c in "\t")
        return v

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    def contabo_configured(self) -> bool:
        return all(
            [
                self.contabo_client_id,
                self.contabo_client_secret,
                self.contabo_api_user,
                self.contabo_api_password,
            ]
        )


def get_settings() -> Settings:
    """Read settings from .env each call so credential updates apply after server restart."""
    return Settings()
