from pydantic import BaseModel, Field


class DomainCheckRequest(BaseModel):
    domains: list[str] = Field(..., min_length=1, max_length=10)


class DomainCheckResult(BaseModel):
    domain: str
    available: bool
    is_premium: bool = False
    premium_registration_price: float = 0
    description: str = ""


class DomainPricing(BaseModel):
    tld: str
    price: float
    currency: str = "USD"
    duration_years: int = 1


class DomainContact(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=255)
    last_name: str = Field(..., min_length=1, max_length=255)
    address1: str = Field(..., min_length=1, max_length=255)
    city: str = Field(..., min_length=1, max_length=50)
    state_province: str = Field(..., min_length=1, max_length=50)
    postal_code: str = Field(..., min_length=1, max_length=50)
    country: str = Field(..., min_length=2, max_length=2)
    phone: str = Field(..., description="Format: +NNN.NNNNNNNNNN")
    email: str
    organization_name: str = ""


class DomainRegisterRequest(BaseModel):
    domain: str = Field(..., min_length=4, max_length=253)
    years: int = Field(default=1, ge=1, le=10)
    whoisguard: bool = False
    contact: DomainContact | None = None


class DomainOut(BaseModel):
    id: int
    domain: str
    status: str
    years: int
    charged_amount: float | None = None
    namecheap_domain_id: str | None = None
    expires_at: str | None = None
    created_at: str

    model_config = {"from_attributes": True}


class DnsRecord(BaseModel):
    host_id: str = ""
    name: str = Field(..., description="Host name, e.g. @ or www")
    type: str = Field(..., description="A, AAAA, CNAME, MX, TXT, etc.")
    address: str
    mx_pref: int = 10
    ttl: int = Field(default=1800, ge=60, le=60000)


class DnsRecordsUpdate(BaseModel):
    records: list[DnsRecord] = Field(..., max_length=50)


class NamecheapStatus(BaseModel):
    configured: bool
    sandbox: bool
    contacts_ready: bool = False
    client_ip: str = ""
    message: str
