import re

MULTI_PART_TLDS = frozenset(
    {
        "co.uk",
        "org.uk",
        "me.uk",
        "com.au",
        "net.au",
        "org.au",
        "co.nz",
        "com.br",
        "co.in",
    }
)


def split_domain(domain: str) -> tuple[str, str]:
    """Split a domain into SLD and TLD for Namecheap DNS APIs."""
    name = domain.strip().lower().rstrip(".")
    parts = name.split(".")
    if len(parts) < 2:
        raise ValueError(f"Invalid domain: {domain}")

    tld2 = ".".join(parts[-2:])
    if tld2 in MULTI_PART_TLDS:
        return ".".join(parts[:-2]), tld2
    return ".".join(parts[:-1]), parts[-1]


def normalize_phone(phone: str) -> str:
    """Format phone for Namecheap API: +NNN.NNNNNNNNNN"""
    raw = phone.strip()
    if not raw:
        raise ValueError("Phone number is required")

    if re.match(r"^\+\d{1,3}\.\d{4,}$", raw):
        return raw

    digits = "".join(c for c in raw if c.isdigit())
    if raw.startswith("+"):
        digits = digits  # already stripped + from join... actually + is not digit so digits is fine
    if not digits:
        raise ValueError(f"Invalid phone number: {phone}")

    # Longest-match country codes (ITU); 1–3 digits
    for length in (3, 2, 1):
        if len(digits) > length:
            return f"+{digits[:length]}.{digits[length:]}"

    raise ValueError(f"Invalid phone number: {phone}")
