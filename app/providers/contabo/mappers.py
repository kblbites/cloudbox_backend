from app.schemas.images import ImageOut
from app.schemas.servers import ServerOut, ServerStatus


STATUS_MAP: dict[str, ServerStatus] = {
    "provisioning": ServerStatus.PROVISIONING,
    "running": ServerStatus.RUNNING,
    "stopped": ServerStatus.STOPPED,
    "error": ServerStatus.ERROR,
    "installing": ServerStatus.INSTALLING,
    "unknown": ServerStatus.UNKNOWN,
}


def map_status(raw: str | None) -> ServerStatus:
    if not raw:
        return ServerStatus.UNKNOWN
    return STATUS_MAP.get(raw.lower(), ServerStatus.OTHER)


def _first_ip(instance: dict, version: int = 4) -> str | None:
    ip_config = instance.get("ipConfig") or instance.get("ip_config")
    if not ip_config:
        return None
    v4 = ip_config.get("v4") or ip_config.get("v4", {})
    if version == 4 and isinstance(v4, dict):
        ips = v4.get("ip") or v4.get("ips") or []
        if isinstance(ips, list) and ips:
            entry = ips[0]
            if isinstance(entry, dict):
                return entry.get("ip")
            return str(entry)
        if isinstance(v4, dict) and v4.get("ip"):
            return v4["ip"]
    return None


def instance_to_server(instance: dict, *, plan_slug: str | None = None) -> ServerOut:
    instance_id = instance.get("instanceId") or instance.get("instance_id")
    return ServerOut(
        id=str(instance_id),
        name=instance.get("name"),
        display_name=instance.get("displayName") or instance.get("display_name"),
        status=map_status(instance.get("status")),
        region=instance.get("region", ""),
        provider="contabo",
        product_id=instance.get("productId") or instance.get("product_id"),
        image_id=instance.get("imageId") or instance.get("image_id"),
        ipv4=_first_ip(instance, 4),
        ipv6=_first_ip(instance, 6),
        created_at=instance.get("createdDate") or instance.get("created_date"),
        os_type=instance.get("osType") or instance.get("os_type"),
        plan_slug=plan_slug,
    )


def image_to_out(item: dict) -> ImageOut:
    return ImageOut(
        id=str(item.get("imageId") or item.get("image_id") or ""),
        name=item.get("name") or item.get("displayName"),
        description=item.get("description"),
        os_type=item.get("osType") or item.get("os_type"),
        version=item.get("version"),
        format=item.get("format"),
        status=item.get("status"),
        standard_image=item.get("standardImage") if "standardImage" in item else item.get("standard_image"),
        size_mb=item.get("sizeMb") or item.get("size_mb"),
        provider="contabo",
    )
