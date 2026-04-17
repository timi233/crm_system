import pytest


pytestmark = pytest.mark.asyncio


async def test_health_returns_200(client):
    response = await client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert "timestamp" in body
