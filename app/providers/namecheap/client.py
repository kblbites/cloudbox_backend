import xml.etree.ElementTree as ET
from typing import Any

import httpx

from app.config import Settings
from app.core.exceptions import ProviderAPIError
from app.providers.namecheap.utils import split_domain


def _tag(local: str) -> str:
    return f"{{http://api.namecheap.com/xml.response}}{local}"


def _text(el: ET.Element | None) -> str:
    return (el.text or "").strip() if el is not None else ""


class NamecheapClient:
    """HTTP client for Namecheap XML API."""

    def __init__(self, settings: Settings):
        self._settings = settings

    @property
    def _base_url(self) -> str:
        if self._settings.namecheap_sandbox:
            return "https://api.sandbox.namecheap.com/xml.response"
        return "https://api.namecheap.com/xml.response"

    def _auth_params(self) -> dict[str, str]:
        return {
            "ApiUser": self._settings.namecheap_api_user,
            "ApiKey": self._settings.namecheap_api_key,
            "UserName": self._settings.namecheap_username,
            "ClientIp": self._settings.namecheap_client_ip,
        }

    async def _call(self, command: str, extra: dict[str, str | int | float | bool] | None = None) -> ET.Element:
        params: dict[str, str] = {**self._auth_params(), "Command": command}
        if extra:
            for key, value in extra.items():
                params[key] = str(value)

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(self._base_url, params=params)
            response.raise_for_status()

        try:
            root = ET.fromstring(response.text)
        except ET.ParseError as exc:
            raise ProviderAPIError("namecheap", f"Invalid XML response: {exc}") from exc

        status = root.get("Status", "")
        if status != "OK":
            errors = [_text(err) for err in root.findall(f".//{_tag('Error')}")]
            msg = "; ".join(e for e in errors if e) or "Namecheap API error"
            if "invalid request ip" in msg.lower():
                configured = self._settings.namecheap_client_ip
                msg = (
                    f"{msg}. Whitelist your public IPv4 in Namecheap → Profile → Tools → "
                    f"API Access → Whitelisted IPs, then set NAMECHEAP_CLIENT_IP to that same "
                    f"address in backend/.env (currently: {configured}). Restart the API server."
                )
            raise ProviderAPIError("namecheap", msg)

        return root

    async def check_domains(self, domains: list[str]) -> list[dict[str, Any]]:
        root = await self._call(
            "namecheap.domains.check",
            {"DomainList": ",".join(domains)},
        )
        results = []
        for node in root.findall(f".//{_tag('DomainCheckResult')}"):
            results.append(
                {
                    "domain": node.get("Domain", ""),
                    "available": node.get("Available", "false").lower() == "true",
                    "is_premium": node.get("IsPremiumName", "false").lower() == "true",
                    "premium_registration_price": float(node.get("PremiumRegistrationPrice") or 0),
                    "description": node.get("Description", ""),
                }
            )
        return results

    async def get_pricing(self, tld: str) -> dict[str, Any]:
        root = await self._call(
            "namecheap.users.getPricing",
            {
                "ProductType": "DOMAIN",
                "ProductCategory": "REGISTER",
                "ProductName": tld.lstrip("."),
            },
        )
        price_node = root.find(f".//{_tag('Price')}")
        if price_node is None:
            raise ProviderAPIError("namecheap", f"No pricing found for .{tld}")
        return {
            "tld": tld.lstrip("."),
            "price": float(price_node.get("Price", "0") or 0),
            "currency": price_node.get("Currency", "USD"),
            "duration_years": int(price_node.get("Duration", "1") or 1),
        }

    async def register_domain(self, params: dict[str, str]) -> dict[str, Any]:
        root = await self._call("namecheap.domains.create", params)
        node = root.find(f".//{_tag('DomainCreateResult')}")
        if node is None:
            raise ProviderAPIError("namecheap", "Missing registration result")
        return {
            "domain": node.get("Domain", ""),
            "registered": node.get("Registered", "false").lower() == "true",
            "charged_amount": float(node.get("ChargedAmount", "0") or 0),
            "domain_id": node.get("DomainID", ""),
            "order_id": node.get("OrderID", ""),
            "transaction_id": node.get("TransactionID", ""),
        }

    async def get_dns_hosts(self, domain: str) -> list[dict[str, Any]]:
        sld, tld = split_domain(domain)
        root = await self._call(
            "namecheap.domains.dns.getHosts",
            {"SLD": sld, "TLD": tld},
        )
        records = []
        for host in root.findall(f".//{_tag('host')}"):
            records.append(
                {
                    "host_id": host.get("HostId", ""),
                    "name": host.get("Name", ""),
                    "type": host.get("Type", ""),
                    "address": host.get("Address", ""),
                    "mx_pref": int(host.get("MXPref", "10") or 10),
                    "ttl": int(host.get("TTL", "1800") or 1800),
                }
            )
        return records

    async def set_dns_hosts(self, domain: str, records: list[dict[str, Any]]) -> bool:
        sld, tld = split_domain(domain)
        extra: dict[str, str | int | float | bool] = {"SLD": sld, "TLD": tld}
        for i, rec in enumerate(records, start=1):
            extra[f"HostName{i}"] = rec["name"]
            extra[f"RecordType{i}"] = rec["type"]
            extra[f"Address{i}"] = rec["address"]
            extra[f"TTL{i}"] = rec.get("ttl", 1800)
            if rec["type"].upper() == "MX":
                extra[f"MXPref{i}"] = rec.get("mx_pref", 10)
        root = await self._call("namecheap.domains.dns.setHosts", extra)
        node = root.find(f".//{_tag('DomainDNSSetHostsResult')}")
        return node is not None and node.get("IsSuccess", "false").lower() == "true"

    async def set_default_nameservers(self, domain: str) -> None:
        sld, tld = split_domain(domain)
        await self._call(
            "namecheap.domains.dns.setDefault",
            {"SLD": sld, "TLD": tld},
        )
