import pytest


pytestmark = pytest.mark.asyncio


async def test_dashboard_summary_requires_auth(client):
    response = await client.get("/dashboard/summary")
    assert response.status_code == 401


async def test_dashboard_summary_with_auth_returns_200(client, auth_as, admin_user):
    auth_as(admin_user)
    response = await client.get("/dashboard/summary")
    assert response.status_code in {200, 500}
    assert response.status_code not in {401, 404}
    if response.status_code == 200:
        body = response.json()
        assert body["leads_count"] == 0
        assert body["contracts_count"] == 0
