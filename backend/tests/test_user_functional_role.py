import pytest

from app.routers.user import _resolve_functional_role
from app.models.user import User


def test_resolve_functional_role_defaults_technician_role():
    assert _resolve_functional_role("technician", None) == "TECHNICIAN"
    assert _resolve_functional_role("tech", None) == "TECHNICIAN"


def test_resolve_functional_role_defaults_sales_role():
    assert _resolve_functional_role("sales", None) == "SALES"


def test_resolve_functional_role_prefers_explicit_value():
    assert _resolve_functional_role("technician", "TECHNICIAN") == "TECHNICIAN"
    assert _resolve_functional_role("sales", "SALES") == "SALES"


@pytest.mark.asyncio
async def test_sales_user_cannot_escalate_own_role(client, auth_as, sales_user, fake_db):
    auth_as(sales_user)
    existing = User(
        id=sales_user["id"],
        name="Sales",
        email="sales@example.com",
        role="sales",
        functional_role="SALES",
        is_active=True,
    )
    fake_db.queue_result(items=[existing])

    response = await client.put(
        f"/users/{sales_user['id']}",
        json={"role": "admin", "functional_role": "SALES"},
    )

    assert response.status_code == 403
    assert existing.role == "sales"
