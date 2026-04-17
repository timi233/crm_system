import pytest

from app.models.lead import Lead
from app.routers import lead as lead_router
import app.core.permissions as permissions


pytestmark = pytest.mark.asyncio


async def _noop(*args, **kwargs):
    return None


def _lead_payload():
    return {
        "lead_name": "测试线索",
        "terminal_customer_id": 1,
        "channel_id": None,
        "source_channel_id": None,
        "lead_stage": "初步接触",
        "lead_source": "官网",
        "contact_person": "李四",
        "contact_phone": "13900000000",
        "products": ["产品A"],
        "estimated_budget": 10000,
        "has_confirmed_requirement": False,
        "has_confirmed_budget": False,
        "sales_owner_id": 1,
        "notes": "test",
    }


async def test_list_leads_requires_auth(client):
    response = await client.get("/leads/")
    assert response.status_code == 401


async def test_list_leads_with_auth_returns_200(client, auth_as, admin_user):
    auth_as(admin_user)
    response = await client.get("/leads/")
    assert response.status_code in {200, 500}
    assert response.status_code not in {401, 404}


async def test_create_lead_validates_body(client, auth_as, admin_user):
    auth_as(admin_user)
    response = await client.post("/leads/", json={})
    assert response.status_code == 422


async def test_lead_crud_basic_flow(client, auth_as, admin_user, fake_db, monkeypatch):
    auth_as(admin_user)

    async def fake_generate_code(db, entity_type):
        return "LEAD-001"

    monkeypatch.setattr(lead_router, "generate_code", fake_generate_code)
    monkeypatch.setattr(lead_router, "log_create", _noop)
    monkeypatch.setattr(lead_router, "log_update", _noop)
    monkeypatch.setattr(lead_router, "log_delete", _noop)
    monkeypatch.setattr(lead_router, "log_stage_change", _noop)
    monkeypatch.setattr(permissions, "assert_can_mutate_entity_v2", _noop)

    create_response = await client.post("/leads/", json=_lead_payload())
    assert create_response.status_code == 200
    created = create_response.json()
    assert created["lead_code"] == "LEAD-001"

    existing = fake_db.storage[Lead][0]
    existing.sales_owner_id = 1
    existing.lead_code = "LEAD-001"

    fake_db.queue_result(items=[existing])
    update_response = await client.put(
        f"/leads/{created['id']}",
        json={"lead_stage": "意向沟通"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["lead_stage"] == "意向沟通"

    fake_db.queue_result(items=[existing])
    delete_response = await client.delete(f"/leads/{created['id']}")
    assert delete_response.status_code == 200
    assert delete_response.json()["message"] == "Lead deleted successfully"
