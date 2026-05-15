import pytest

pytestmark = pytest.mark.asyncio


async def test_feishu_status_requires_auth(client):
    response = await client.get("/integrations/feishu/status")
    assert response.status_code == 401


async def test_feishu_status_requires_admin(client, auth_as, sales_user, fake_db):
    auth_as(sales_user)
    response = await client.get("/integrations/feishu/status")
    assert response.status_code == 403


async def test_feishu_status_admin_ok(client, auth_as, admin_user, fake_db):
    auth_as(admin_user)
    response = await client.get("/integrations/feishu/status")
    assert response.status_code == 200
    data = response.json()
    assert "configured" in data
    assert "ws_enabled" in data


async def test_feishu_check_requires_admin(client, auth_as, sales_user, fake_db):
    auth_as(sales_user)
    response = await client.post("/integrations/feishu/check")
    assert response.status_code == 403


async def test_feishu_check_admin_ok(client, auth_as, admin_user, fake_db):
    auth_as(admin_user)
    response = await client.post("/integrations/feishu/check")
    assert response.status_code == 200
    data = response.json()
    assert "configured" in data
    assert "tenant_token_ok" in data
    assert "app_token_ok" in data
    assert "ws_running" in data


async def test_feishu_diagnostics_service_configured():
    from app.services.feishu_diagnostics_service import feishu_diagnostics_service

    result = await feishu_diagnostics_service.check_configuration()
    assert "configured" in result
    assert "ws_enabled" in result


async def test_feishu_diagnostics_service_full_check():
    from app.services.feishu_diagnostics_service import feishu_diagnostics_service

    result = await feishu_diagnostics_service.full_check()
    assert "configured" in result
    assert "tenant_token_ok" in result
    assert "app_token_ok" in result
    assert "ws_running" in result


async def test_feishu_ws_service_status():
    from app.services.feishu_ws_service import feishu_ws_service

    status = feishu_ws_service.get_status()
    assert "running" in status
    assert isinstance(status["running"], bool)