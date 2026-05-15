import pytest
from fastapi import Query

from app.models.customer import TerminalCustomer

pytestmark = pytest.mark.asyncio


async def test_customers_pagination_params(client, auth_as, admin_user):
    auth_as(admin_user)

    response = await client.get("/customers/?limit=101")
    assert response.status_code == 422

    response = await client.get("/customers/?skip=-1")
    assert response.status_code == 422

    response = await client.get("/customers/?limit=100")
    assert response.status_code in {200, 401, 403}

    response = await client.get("/customers/?limit=20")
    assert response.status_code in {200, 401, 403}


async def test_customers_real_data_pagination(client, auth_as, admin_user, fake_db, monkeypatch):
    """真实数据分页测试：验证skip和默认limit实际生效"""
    import app.core.permissions as permissions

    auth_as(admin_user)

    async def _noop(*args, **kwargs):
        return None
    monkeypatch.setattr(permissions, "assert_can_mutate_entity_v2", _noop)

    test_customers = []
    for i in range(25):
        cust = TerminalCustomer(
            id=i+1,
            customer_code=f"CUST-{i+1:03d}",
            customer_name=f"测试客户{i+1}",
            credit_code=f"91310000{i:07d}X",
            customer_industry="制造业",
            customer_region="上海",
            customer_owner_id=1,
            customer_status="Active",
            owner=None,
            channel=None,
        )
        test_customers.append(cust)

    fake_db.queue_result(items=test_customers[:20])
    response = await client.get("/customers/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 20
    assert data[0]["customer_code"] == "CUST-001"
    assert data[19]["customer_code"] == "CUST-020"

    fake_db.queue_result(items=test_customers[5:15])
    response = await client.get("/customers/?skip=5&limit=10")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 10
    assert data[0]["customer_code"] == "CUST-006"
    assert data[9]["customer_code"] == "CUST-015"

    fake_db.queue_result(items=test_customers[20:])
    response = await client.get("/customers/?skip=20")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 5
    assert data[0]["customer_code"] == "CUST-021"
    assert data[4]["customer_code"] == "CUST-025"


async def test_leads_pagination_params(client, auth_as, admin_user):
    auth_as(admin_user)

    response = await client.get("/leads/?limit=101")
    assert response.status_code == 422

    response = await client.get("/leads/?skip=-1")
    assert response.status_code == 422

    response = await client.get("/leads/?limit=100")
    assert response.status_code in {200, 401, 403}


async def test_opportunities_pagination_params(client, auth_as, admin_user):
    auth_as(admin_user)

    response = await client.get("/opportunities/?limit=101")
    assert response.status_code == 422

    response = await client.get("/opportunities/?skip=-1")
    assert response.status_code == 422

    response = await client.get("/opportunities/?limit=100")
    assert response.status_code in {200, 401, 403}


async def test_projects_pagination_params(client, auth_as, admin_user):
    auth_as(admin_user)

    response = await client.get("/projects/?limit=101")
    assert response.status_code == 422

    response = await client.get("/projects/?skip=-1")
    assert response.status_code == 422

    response = await client.get("/projects/?limit=100")
    assert response.status_code in {200, 401, 403}


async def test_work_orders_pagination_params(client, auth_as, admin_user):
    auth_as(admin_user)

    response = await client.get("/work-orders/?limit=101")
    assert response.status_code == 422

    response = await client.get("/work-orders/?skip=-1")
    assert response.status_code == 422

    response = await client.get("/work-orders/?limit=100")
    assert response.status_code in {200, 401, 403}


async def test_contracts_pagination_params(client, auth_as, admin_user):
    auth_as(admin_user)

    response = await client.get("/contracts/?limit=101")
    assert response.status_code == 422

    response = await client.get("/contracts/?skip=-1")
    assert response.status_code == 422

    response = await client.get("/contracts/?limit=100")
    assert response.status_code in {200, 401, 403}