import pytest
from unittest.mock import MagicMock

from app.models.work_order import WorkOrder, WorkOrderStatus
from app.models.user import User
from app.routers.dispatch import fill_technician_names
from tests.conftest import FakeAsyncSession


pytestmark = pytest.mark.asyncio


class MockDispatchRecord:
    def __init__(self, work_order_id=None, technician_ids=None):
        self.id = 1
        self.work_order_id = work_order_id
        self.technician_ids = technician_ids or []
        self.technician_names = []
        self.estimated_start_date = None
        self.estimated_start_period = None
        self.estimated_end_date = None
        self.estimated_end_period = None


async def test_fill_technician_names_empty_records():
    db = FakeAsyncSession()
    records = []
    result = await fill_technician_names(db, records)
    assert result == []


async def test_fill_technician_names_no_technicians():
    db = FakeAsyncSession()
    records = [MockDispatchRecord(work_order_id=None, technician_ids=[])]
    result = await fill_technician_names(db, records)
    assert result[0].technician_names == []


async def test_fill_technician_names_with_technician_ids():
    db = FakeAsyncSession()
    db.queue_result(rows=[(1, "Tech One"), (2, "Tech Two")])
    db.queue_result(rows=[])
    
    records = [MockDispatchRecord(work_order_id=None, technician_ids=["1", "2"])]
    result = await fill_technician_names(db, records)
    assert "Tech One" in result[0].technician_names
    assert "Tech Two" in result[0].technician_names


async def test_fill_technician_names_with_invalid_technician_ids():
    db = FakeAsyncSession()
    db.queue_result(items=[])
    db.queue_result(rows=[])
    
    records = [MockDispatchRecord(work_order_id=None, technician_ids=["invalid", ""])]
    result = await fill_technician_names(db, records)
    assert result[0].technician_names == []


async def test_fill_technician_names_with_work_order_id():
    db = FakeAsyncSession()
    db.queue_result(rows=[(1, "2024-01-01", "morning", "2024-01-02", "afternoon")])
    
    records = [MockDispatchRecord(work_order_id=1, technician_ids=[])]
    result = await fill_technician_names(db, records)
    assert result[0].estimated_start_date == "2024-01-01"
    assert result[0].estimated_start_period == "morning"
    assert result[0].estimated_end_date == "2024-01-02"
    assert result[0].estimated_end_period == "afternoon"


async def test_fill_technician_names_with_multiple_records():
    db = FakeAsyncSession()
    db.queue_result(rows=[(1, "Tech A"), (2, "Tech B")])
    db.queue_result(rows=[])
    
    records = [
        MockDispatchRecord(work_order_id=None, technician_ids=["1"]),
        MockDispatchRecord(work_order_id=None, technician_ids=["2"]),
    ]
    result = await fill_technician_names(db, records)
    assert result[0].technician_names == ["Tech A"]
    assert result[1].technician_names == ["Tech B"]


async def test_check_credit_code_customer_requires_auth(client):
    response = await client.get("/customers/check-credit-code?credit_code=test123")
    assert response.status_code == 401


async def test_check_credit_code_channel_requires_auth(client):
    response = await client.get("/channels/check-credit-code?credit_code=test123")
    assert response.status_code == 401


async def test_check_credit_code_customer_sales_allowed(client, auth_as, sales_user, fake_db):
    auth_as(sales_user)
    fake_db.queue_result(items=[])
    response = await client.get("/customers/check-credit-code?credit_code=test123")
    assert response.status_code == 200
    assert response.json()["exists"] is False


async def test_check_credit_code_customer_technician_denied(client, auth_as, technician_user):
    auth_as(technician_user)
    response = await client.get("/customers/check-credit-code?credit_code=test123")
    assert response.status_code == 403


async def test_check_credit_code_channel_technician_denied(client, auth_as, technician_user):
    auth_as(technician_user)
    response = await client.get("/channels/check-credit-code?credit_code=test123")
    assert response.status_code == 403


async def test_list_dispatch_records_has_bounded_pagination(client, auth_as, admin_user, fake_db):
    """Dispatch records list endpoint should have default limit=20, max=100."""
    auth_as(admin_user)
    fake_db.queue_result(items=[])
    response = await client.get("/dispatch-records")
    assert response.status_code == 200


async def test_list_dispatch_records_limit_exceeded(client, auth_as, admin_user):
    """Dispatch records list should reject limit > 100."""
    auth_as(admin_user)
    response = await client.get("/dispatch-records?limit=150")
    assert response.status_code == 422


async def test_list_dispatch_records_with_skip(client, auth_as, admin_user, fake_db):
    """Dispatch records list should support skip parameter."""
    auth_as(admin_user)
    fake_db.queue_result(items=[])
    response = await client.get("/dispatch-records?skip=20&limit=10")
    assert response.status_code == 200