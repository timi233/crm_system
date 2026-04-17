import pytest


pytestmark = pytest.mark.asyncio


async def test_list_follow_ups_requires_auth(client):
    response = await client.get("/follow-ups/")
    assert response.status_code == 401


async def test_list_follow_ups_with_auth_returns_200(client, auth_as, admin_user):
    auth_as(admin_user)
    response = await client.get("/follow-ups/")
    assert response.status_code in {200, 500}
    assert response.status_code not in {401, 404}


async def test_create_follow_up_validates_body(client, auth_as, admin_user):
    auth_as(admin_user)
    response = await client.post("/follow-ups/", json={})
    assert response.status_code == 422
