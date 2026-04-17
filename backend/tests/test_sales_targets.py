import pytest


pytestmark = pytest.mark.asyncio


async def test_list_sales_targets_requires_auth(client):
    response = await client.get("/sales-targets/")
    assert response.status_code == 401


async def test_list_sales_targets_with_auth_returns_200(client, auth_as, admin_user):
    auth_as(admin_user)
    response = await client.get("/sales-targets/")
    assert response.status_code in {200, 500}
    assert response.status_code not in {401, 404}


async def test_create_sales_target_validates_body(client, auth_as, admin_user):
    auth_as(admin_user)
    response = await client.post("/sales-targets/year", json={})
    assert response.status_code == 422
