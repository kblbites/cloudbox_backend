from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.core.exceptions import CloudBoxError, ProviderAPIError, ProviderNotConfiguredError
from app.db.models import DomainRecord, User
from app.providers.namecheap.client import NamecheapClient
from app.providers.namecheap.utils import normalize_phone
from app.schemas.domains import DomainContact, DomainRegisterRequest
from fastapi import status


class DomainService:
    def __init__(self, settings: Settings | None = None):
        self._settings = settings or get_settings()

    def _client(self) -> NamecheapClient:
        if not self._settings.namecheap_configured():
            raise ProviderNotConfiguredError("namecheap")
        return NamecheapClient(self._settings)

    def status(self) -> dict:
        configured = self._settings.namecheap_configured()
        contacts = self._settings.namecheap_contacts_configured()
        if not configured:
            msg = (
                "Set NAMECHEAP_API_USER, NAMECHEAP_API_KEY, NAMECHEAP_USERNAME, "
                "and NAMECHEAP_CLIENT_IP (whitelisted IPv4) in backend/.env"
            )
        elif not contacts:
            msg = "Namecheap API ready. Add NAMECHEAP_CONTACT_* fields for domain registration."
        else:
            msg = "Namecheap API and registrant contacts configured."
        client_ip = self._settings.namecheap_client_ip if configured else ""
        if configured and client_ip in ("127.0.0.1", "localhost", ""):
            msg = (
                f"NAMECHEAP_CLIENT_IP must be your public IPv4 whitelisted in Namecheap "
                f"(not {client_ip or 'empty'}). Namecheap rejects 127.0.0.1."
            )
        return {
            "configured": configured,
            "sandbox": self._settings.namecheap_sandbox,
            "contacts_ready": contacts,
            "client_ip": client_ip,
            "message": msg,
        }

    async def check_availability(self, domains: list[str]) -> list[dict]:
        client = self._client()
        try:
            return await client.check_domains(domains)
        except ProviderAPIError as exc:
            raise CloudBoxError(str(exc.message), status_code=status.HTTP_502_BAD_GATEWAY) from exc

    async def get_pricing(self, tld: str) -> dict:
        client = self._client()
        try:
            return await client.get_pricing(tld)
        except ProviderAPIError as exc:
            raise CloudBoxError(str(exc.message), status_code=status.HTTP_502_BAD_GATEWAY) from exc

    def _build_contact_params(self, contact: DomainContact) -> dict[str, str]:
        try:
            phone = normalize_phone(contact.phone)
        except ValueError as exc:
            raise CloudBoxError(
                f"Invalid contact phone: {exc}. Use format +NNN.NNNNNNNNNN (e.g. +250.787490069)",
                status_code=status.HTTP_400_BAD_REQUEST,
            ) from exc

        prefix_sets = ("Registrant", "Tech", "Admin", "AuxBilling")
        params: dict[str, str] = {}
        for prefix in prefix_sets:
            params[f"{prefix}FirstName"] = contact.first_name
            params[f"{prefix}LastName"] = contact.last_name
            params[f"{prefix}Address1"] = contact.address1
            params[f"{prefix}City"] = contact.city
            params[f"{prefix}StateProvince"] = contact.state_province
            params[f"{prefix}PostalCode"] = contact.postal_code
            params[f"{prefix}Country"] = contact.country
            params[f"{prefix}Phone"] = phone
            params[f"{prefix}EmailAddress"] = contact.email
            if contact.organization_name:
                params[f"{prefix}OrganizationName"] = contact.organization_name
        return params

    def _default_contact(self, user: User) -> DomainContact:
        s = self._settings
        if not s.namecheap_contacts_configured():
            raise CloudBoxError(
                "Registrant contact not configured. Set NAMECHEAP_CONTACT_* in .env "
                "or pass contact in the registration request.",
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        return DomainContact(
            first_name=s.namecheap_contact_first_name,
            last_name=s.namecheap_contact_last_name,
            address1=s.namecheap_contact_address1,
            city=s.namecheap_contact_city,
            state_province=s.namecheap_contact_state,
            postal_code=s.namecheap_contact_postal_code,
            country=s.namecheap_contact_country,
            phone=s.namecheap_contact_phone,
            email=s.namecheap_contact_email or user.email,
            organization_name=s.namecheap_contact_organization,
        )

    async def register_domain(
        self,
        db: Session,
        user: User,
        payload: DomainRegisterRequest,
    ) -> DomainRecord:
        domain = payload.domain.strip().lower()
        existing = db.query(DomainRecord).filter(DomainRecord.domain == domain).first()
        if existing:
            raise CloudBoxError("Domain already registered in CloudBox", status_code=status.HTTP_400_BAD_REQUEST)

        client = self._client()
        checks = await client.check_domains([domain])
        if not checks or not checks[0].get("available"):
            raise CloudBoxError(
                f"Domain {domain} is not available for registration",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        check = checks[0]
        contact = payload.contact or self._default_contact(user)
        params: dict[str, str] = {
            "DomainName": domain,
            "Years": str(payload.years),
            "AddFreeWhoisguard": "yes" if payload.whoisguard else "no",
            "WGEnabled": "yes" if payload.whoisguard else "no",
            **self._build_contact_params(contact),
        }
        if check.get("is_premium"):
            params["IsPremiumDomain"] = "true"
            params["PremiumPrice"] = str(check.get("premium_registration_price", 0))

        try:
            result = await client.register_domain(params)
        except ProviderAPIError as exc:
            raise CloudBoxError(str(exc.message), status_code=status.HTTP_502_BAD_GATEWAY) from exc

        if not result.get("registered"):
            raise CloudBoxError("Domain registration failed", status_code=status.HTTP_502_BAD_GATEWAY)

        try:
            await client.set_default_nameservers(domain)
        except ProviderAPIError:
            pass

        record = DomainRecord(
            user_id=user.id,
            domain=domain,
            status="active",
            years=payload.years,
            charged_amount=result.get("charged_amount"),
            namecheap_domain_id=result.get("domain_id"),
            namecheap_order_id=result.get("order_id"),
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    def list_domains(self, db: Session, user: User) -> list[DomainRecord]:
        return (
            db.query(DomainRecord)
            .filter(DomainRecord.user_id == user.id)
            .order_by(DomainRecord.created_at.desc())
            .all()
        )

    def get_domain(self, db: Session, user: User, domain: str) -> DomainRecord:
        record = (
            db.query(DomainRecord)
            .filter(DomainRecord.user_id == user.id, DomainRecord.domain == domain.lower())
            .first()
        )
        if not record:
            raise CloudBoxError("Domain not found", status_code=status.HTTP_404_NOT_FOUND)
        return record

    async def get_dns(self, user: User, domain: str, db: Session) -> list[dict]:
        self.get_domain(db, user, domain)
        client = self._client()
        try:
            return await client.get_dns_hosts(domain)
        except ProviderAPIError as exc:
            raise CloudBoxError(str(exc.message), status_code=status.HTTP_502_BAD_GATEWAY) from exc

    async def update_dns(
        self,
        user: User,
        domain: str,
        db: Session,
        records: list[dict],
    ) -> bool:
        self.get_domain(db, user, domain)
        client = self._client()
        try:
            return await client.set_dns_hosts(domain, records)
        except ProviderAPIError as exc:
            raise CloudBoxError(str(exc.message), status_code=status.HTTP_502_BAD_GATEWAY) from exc
