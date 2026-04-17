import pytest


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
