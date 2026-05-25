from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class ServerStatus(str, Enum):
    PROVISIONING = "provisioning"
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"
    INSTALLING = "installing"
    UNKNOWN = "unknown"
    OTHER = "other"


class ServerAction(str, Enum):
    START = "start"
    STOP = "stop"
    RESTART = "restart"
    SHUTDOWN = "shutdown"


class ServerOut(BaseModel):
    id: str
    name: str | None = None
    display_name: str | None = None
    status: ServerStatus
    region: str
    provider: str
    product_id: str | None = None
    image_id: str | None = None
    ipv4: str | None = None
    ipv6: str | None = None
    created_at: str | None = None
    os_type: str | None = None
    plan_slug: str | None = None


class ServerCreate(BaseModel):
    """Unified create payload aligned with the CloudBox UI wizard."""

    display_name: str = Field(..., max_length=255)
    plan_slug: Literal["basic", "standard", "premium", "business"] = "basic"
    region: str = Field(default="EU", description="Provider region code (e.g. EU, US-central)")
    image_id: str | None = Field(
        default=None,
        description="OS image UUID; provider default used if omitted",
    )
    period_months: Literal[1, 3, 6, 12] = 1
    region_id: str | None = Field(
        default=None,
        description="Display region id (e.g. kigali); resolved to provider code",
    )
    ssh_key_ids: list[int] = Field(default_factory=list)
    ssh_public_key: str | None = Field(
        default=None,
        description="OpenSSH public key; stored as Contabo secret on provision",
    )
    root_password_secret_id: int | None = None
    root_password: str | None = Field(
        default=None,
        min_length=8,
        max_length=128,
        description="Root/admin password; stored as Contabo secret on provision",
    )
    auth_method: Literal["password", "ssh_key"] = "password"
    user_data: str | None = None
    default_user: Literal["admin", "root", "administrator"] = "admin"
    provider: str | None = Field(
        default=None,
        description="Override default provider for this request",
    )
