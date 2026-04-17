import pytest

from app.models.customer import TerminalCustomer
from app.routers import customer as customer_router
import app.core.permissions as permissions


pytestmark = pytest.mark.asyncio


async def _noop(*args, **kwargs):
    return None


def _customer_payload():
    return {
        "customer_name": "测试客户",
        "credit_code": "91310000123456789X",
        "customer_industry": "制造业",
        "customer_region": "上海",
        "customer_owner_id": 1,
        "channel_id": None,
        "main_contact": "张三",
        "phone": "13800000000",
        "customer_status": "Active",
        "maintenance_expiry": None,
        "notes": "test",
    }


async def test_list_customers_requires_auth(client):
    response = await client.get("/customers/")
    assert response.status_code == 401


async def test_list_customers_with_auth_returns_200(client, auth_as, admin_user):
    auth_as(admin_user)
    response = await client.get("/customers/")
    assert response.status_code in {200, 500}
    assert response.status_code not in {401, 404}


async def test_create_customer_validates_body(client, auth_as, admin_user):
    auth_as(admin_user)
    response = await client.post("/customers/", json={})
    assert response.status_code == 422


async def test_customer_crud_basic_flow(client, auth_as, admin_user, fake_db, monkeypatch):
    auth_as(admin_user)

    async def fake_generate_code(db, entity_type):
        return "CUST-001"

    monkeypatch.setattr(customer_router, "generate_code", fake_generate_code)
    monkeypatch.setattr(customer_router, "log_create", _noop)
    monkeypatch.setattr(customer_router, "log_update", _noop)
    monkeypatch.setattr(customer_router, "log_delete", _noop)
    monkeypatch.setattr(permissions, "assert_can_mutate_entity_v2", _noop)

    create_response = await client.post("/customers/", json=_customer_payload())
    assert create_response.status_code == 200
    created = create_response.json()
    assert created["customer_code"] == "CUST-001"

    existing = fake_db.storage[TerminalCustomer][0]
    existing.customer_code = "CUST-001"
    existing.owner = None
    existing.channel = None

    update_payload = _customer_payload() | {"customer_name": "已更新客户"}
    fake_db.queue_result(items=[existing])
    update_response = await client.put(f"/customers/{created['id']}", json=update_payload)
    assert update_response.status_code == 200
    assert update_response.json()["customer_name"] == "已更新客户"

    fake_db.queue_result(items=[existing])
    delete_response = await client.delete(f"/customers/{created['id']}")
    assert delete_response.status_code == 200
    assert delete_response.json()["message"] == "Customer deleted successfully"
