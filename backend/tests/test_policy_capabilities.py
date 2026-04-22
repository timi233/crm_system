import pytest


pytestmark = pytest.mark.asyncio


async def test_me_capabilities_requires_auth(client):
    response = await client.get("/auth/me/capabilities")
    assert response.status_code == 401


async def test_me_capabilities_for_admin(client, auth_as, admin_user):
    auth_as(admin_user)

    response = await client.get("/auth/me/capabilities")

    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "admin"
    assert data["capabilities"]["user:create"] is True
    assert data["capabilities"]["channel:create"] is True
    assert data["capabilities"]["channel:read"] is True
    assert data["capabilities"]["channel_performance:read"] is True
    assert data["capabilities"]["channel_training:read"] is True
    assert data["capabilities"]["channel_performance:manage"] is True
    assert data["capabilities"]["channel_training:manage"] is True
    assert data["capabilities"]["dashboard:team_rank"] is True


async def test_me_capabilities_for_sales(client, auth_as, sales_user):
    auth_as(sales_user)

    response = await client.get("/auth/me/capabilities")

    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "sales"
    assert data["capabilities"]["lead:create"] is True
    assert data["capabilities"]["customer:create"] is True
    assert data["capabilities"]["channel:create"] is True
    assert data["capabilities"]["channel:read"] is True
    assert data["capabilities"]["channel_performance:read"] is True
    assert data["capabilities"]["channel_training:read"] is True
    assert data["capabilities"]["channel_performance:manage"] is True
    assert data["capabilities"]["channel_training:manage"] is True
    assert data["capabilities"]["dashboard:team_rank"] is False
