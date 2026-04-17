import pytest

from app.routers.alert import AlertService


pytestmark = pytest.mark.asyncio


async def test_get_alerts_requires_auth(client):
    response = await client.get("/alerts")
    assert response.status_code == 401


async def test_get_alerts_with_auth_returns_200(client, auth_as, admin_user, monkeypatch):
    auth_as(admin_user)

    async def fake_calculate_alerts(db, user_id, is_admin):
        return []

    monkeypatch.setattr(AlertService, "calculate_alerts", fake_calculate_alerts)
    response = await client.get("/alerts")
    assert response.status_code == 200
    assert response.json() == []


async def test_create_alert_rule_validates_body(client, auth_as, admin_user):
    auth_as(admin_user)
    response = await client.post("/alert-rules", json={})
    assert response.status_code == 422
