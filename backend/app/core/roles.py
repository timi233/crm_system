from typing import Final


ROLE_ADMIN: Final[str] = "admin"
ROLE_SALES: Final[str] = "sales"
ROLE_BUSINESS: Final[str] = "business"
ROLE_FINANCE: Final[str] = "finance"
ROLE_TECHNICIAN: Final[str] = "technician"

LEGACY_ROLE_ALIASES: Final[dict[str, str]] = {
    "tech": ROLE_TECHNICIAN,
}

PRIMARY_ROLES: Final[tuple[str, ...]] = (
    ROLE_ADMIN,
    ROLE_SALES,
    ROLE_BUSINESS,
    ROLE_FINANCE,
    ROLE_TECHNICIAN,
)


def normalize_role(role: str | None) -> str | None:
    if role is None:
        return None
    return LEGACY_ROLE_ALIASES.get(role, role)

