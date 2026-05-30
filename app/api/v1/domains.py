from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_user
from app.core.exceptions import CloudBoxError, to_http_exception
from app.db.database import get_db
from app.db.models import DomainRecord, User
from app.schemas.domains import (
    DnsRecord,
    DnsRecordsUpdate,
    DomainCheckRequest,
    DomainCheckResult,
    DomainOut,
    DomainPricing,
    DomainRegisterRequest,
    NamecheapStatus,
)
from app.services.domains import DomainService
from sqlalchemy.orm import Session

router = APIRouter()


def get_domain_service() -> DomainService:
    return DomainService()


def _domain_out(record: DomainRecord) -> DomainOut:
    return DomainOut(
        id=record.id,
        domain=record.domain,
        status=record.status,
        years=record.years,
        charged_amount=record.charged_amount,
        namecheap_domain_id=record.namecheap_domain_id,
        expires_at=None,
        created_at=record.created_at.isoformat() if record.created_at else "",
    )


@router.get("/status", response_model=NamecheapStatus)
def namecheap_status(
    service: DomainService = Depends(get_domain_service),
) -> NamecheapStatus:
    data = service.status()
    return NamecheapStatus(
        configured=data["configured"],
        sandbox=data["sandbox"],
        contacts_ready=data.get("contacts_ready", False),
        client_ip=data.get("client_ip", ""),
        message=data["message"],
    )


@router.post("/check", response_model=list[DomainCheckResult])
async def check_domains(
    payload: DomainCheckRequest,
    _user: User = Depends(get_current_user),
    service: DomainService = Depends(get_domain_service),
) -> list[DomainCheckResult]:
    try:
        results = await service.check_availability(payload.domains)
        return [DomainCheckResult(**r) for r in results]
    except CloudBoxError as exc:
        raise to_http_exception(exc) from exc


@router.get("/pricing", response_model=DomainPricing)
async def domain_pricing(
    tld: str = Query("com", min_length=2, max_length=20),
    _user: User = Depends(get_current_user),
    service: DomainService = Depends(get_domain_service),
) -> DomainPricing:
    try:
        data = await service.get_pricing(tld)
        return DomainPricing(**data)
    except CloudBoxError as exc:
        raise to_http_exception(exc) from exc


@router.get("", response_model=list[DomainOut])
def list_domains(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    service: DomainService = Depends(get_domain_service),
) -> list[DomainOut]:
    records = service.list_domains(db, user)
    return [_domain_out(r) for r in records]


@router.post("/register", response_model=DomainOut, status_code=201)
async def register_domain(
    payload: DomainRegisterRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    service: DomainService = Depends(get_domain_service),
) -> DomainOut:
    try:
        record = await service.register_domain(db, user, payload)
        return _domain_out(record)
    except CloudBoxError as exc:
        raise to_http_exception(exc) from exc


@router.get("/{domain}/dns", response_model=list[DnsRecord])
async def get_domain_dns(
    domain: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    service: DomainService = Depends(get_domain_service),
) -> list[DnsRecord]:
    try:
        records = await service.get_dns(user, domain, db)
        return [DnsRecord(**r) for r in records]
    except CloudBoxError as exc:
        raise to_http_exception(exc) from exc


@router.put("/{domain}/dns")
async def update_domain_dns(
    domain: str,
    payload: DnsRecordsUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    service: DomainService = Depends(get_domain_service),
) -> dict[str, bool]:
    try:
        ok = await service.update_dns(
            user,
            domain,
            db,
            [r.model_dump() for r in payload.records],
        )
        return {"success": ok}
    except CloudBoxError as exc:
        raise to_http_exception(exc) from exc
