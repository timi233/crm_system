import pytest

from app.models.user import User


pytestmark = pytest.mark.asyncio


async def test_login_with_wrong_credentials_returns_401(client):
    response = await client.post(
        "/auth/login",
        data={"username": "nobody@example.com", "password": "bad-password"},
    )
    assert response.status_code == 401


async def test_get_feishu_url_returns_200(client):
    response = await client.get("/auth/feishu/url")
    assert response.status_code == 200
    assert "url" in response.json()


async def test_get_me_capabilities_without_auth_returns_401(client):
    response = await client.get("/auth/me/capabilities")
    assert response.status_code == 401


async def test_feishu_login_rejects_unregistered_user(client, fake_db, monkeypatch):
    async def fake_get_user_by_code(code):
        return {
            "open_id": "ou_new_user",
            "union_id": "on_new_user",
            "name": "New User",
            "email": "new@example.com",
            "mobile": "13800138000",
            "avatar_url": "",
        }

    monkeypatch.setattr(
        "app.routers.auth.feishu_service.get_user_by_code",
        fake_get_user_by_code,
    )
    fake_db.queue_result(items=[])
    fake_db.queue_result(items=[])
    fake_db.queue_result(items=[])
    fake_db.queue_result(items=[])

    response = await client.post(
        "/auth/feishu/login",
        json={"code": "tmp-code", "state": "state"},
    )

    assert response.status_code == 403
    assert "未同步" in response.json()["detail"]


async def test_feishu_login_binds_pre_registered_email_user(client, fake_db, monkeypatch):
    async def fake_get_user_by_code(code):
        return {
            "open_id": "ou_existing_user",
            "union_id": "on_existing_user",
            "name": "Existing User",
            "email": "existing@example.com",
            "mobile": "13800138001",
            "avatar_url": "https://example.com/avatar.png",
        }

    monkeypatch.setattr(
        "app.routers.auth.feishu_service.get_user_by_code",
        fake_get_user_by_code,
    )
    user = User(
        id=10,
        email="existing@example.com",
        name="Old Name",
        role="sales",
        is_active=True,
    )
    fake_db.queue_result(items=[])
    fake_db.queue_result(items=[])
    fake_db.queue_result(items=[])
    fake_db.queue_result(items=[user])

    response = await client.post(
        "/auth/feishu/login",
        json={"code": "tmp-code", "state": "state"},
    )

    assert response.status_code == 200
    assert user.feishu_id == "ou_existing_user"
    assert response.json()["user"]["name"] == "Existing User"
