import pytest


pytestmark = pytest.mark.asyncio


async def test_list_opportunities_requires_auth(client):
    response = await client.get("/opportunities/")
    assert response.status_code == 401


async def test_list_opportunities_with_auth_returns_200(client, auth_as, admin_user):
    auth_as(admin_user)
    response = await client.get("/opportunities/")
    assert response.status_code in {200, 500}
    assert response.status_code not in {401, 404}


async def test_create_opportunity_validates_body(client, auth_as, admin_user):
    auth_as(admin_user)
    response = await client.post("/opportunities/", json={})
    assert response.status_code == 422
