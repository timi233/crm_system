import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.feishu_org_sync_service import FeishuOrgSyncService
from app.services.handover_service import HandoverService
from app.models.user import User, FeishuEmploymentStatus
from app.models.feishu_org_sync_run import FeishuOrgSyncRun
from app.models.employee_handover_request import EmployeeHandoverRequest, HandoverRequestStatus
from app.models.employee_handover_log import EmployeeHandoverLog
from app.models.customer import TerminalCustomer
from app.models.lead import Lead


pytestmark = pytest.mark.asyncio


class MockAsyncSession:
    def __init__(self):
        self._stored = {}
        self._queued_results = []
        self._id_counter = 1

    def queue_result(self, items):
        self._queued_results.append(items)

    async def execute(self, query):
        if self._queued_results:
            return MockScalarResult(self._queued_results.pop(0))
        return MockScalarResult([])

    def add(self, obj):
        if not hasattr(obj, "id") or obj.id is None:
            obj.id = self._id_counter
            self._id_counter += 1
        model_type = type(obj).__name__
        self._stored.setdefault(model_type, []).append(obj)

    async def commit(self):
        return None

    async def rollback(self):
        return None

    async def flush(self):
        return None

    async def refresh(self, obj, attrs=None):
        return None

    async def scalar(self):
        return self._queued_results[-1][0] if self._queued_results else 0


class MockScalarResult:
    def __init__(self, items):
        self._items = list(items)

    def scalar_one_or_none(self):
        return self._items[0] if self._items else None

    def scalars(self):
        return MockScalarsResult(self._items)

    def scalar(self):
        return self._items[0] if self._items else 0


class MockScalarsResult:
    def __init__(self, items):
        self._items = items

    def all(self):
        return self._items


async def test_first_sync_no_departure_detection():
    mock_db = MockAsyncSession()

    mock_departments = [{"open_department_id": "dept_1", "name": "Dept"}]
    mock_members = [{"open_id": "ou_1", "name": "User 1"}]

    with patch("app.services.feishu_org_sync_service.feishu_service") as mock_feishu:
        mock_feishu.get_departments = AsyncMock(return_value=mock_departments)
        mock_feishu.get_department_members = AsyncMock(return_value=mock_members)

        mock_db.queue_result([])

        sync_service = FeishuOrgSyncService(mock_db)
        result = await sync_service.sync_users_with_tracking()

    assert result["left_detected"] == 0
    assert result["left_threshold_exceeded"] is False


async def test_departure_threshold_logic():
    mock_db = MockAsyncSession()

    sync_service = FeishuOrgSyncService(mock_db)

    seen_ids = set()
    sync_run = FeishuOrgSyncRun(id=2, status="running")

    mock_db.queue_result([FeishuOrgSyncRun(id=1, status="success")])
    mock_db.queue_result([])

    result = await sync_service._detect_departures(seen_ids, sync_run)

    assert result["left_detected"] == 0
    assert result["threshold_exceeded"] is False


async def test_handover_execute_status_change():
    mock_db = MockAsyncSession()

    handover_request = EmployeeHandoverRequest(
        id=1, from_user_id=10, to_user_id=20,
        status=HandoverRequestStatus.PENDING_EXECUTION
    )

    from_user = User(id=10, name="离职员工")
    customer = TerminalCustomer(
        id=100,
        customer_code="C001",
        customer_name="客户",
        credit_code="123456789012345678",
        customer_industry="IT",
        customer_region="上海",
        customer_owner_id=10,
        customer_status="active",
        notes="原备注",
    )

    mock_db.queue_result([from_user])
    mock_db.queue_result([customer])
    for _ in range(8):
        mock_db.queue_result([])

    service = HandoverService(mock_db)
    result = await service.execute_handover(handover_request)

    assert result["success"] is True
    assert handover_request.status == HandoverRequestStatus.COMPLETED
    assert customer.customer_owner_id == 20
    assert "交接自离职员工" in customer.notes
    logs = mock_db._stored["EmployeeHandoverLog"]
    assert logs[0].entity_type == "TerminalCustomer"
    assert logs[0].remark_appended == "交接自离职员工"


async def test_handover_execute_respects_scope_config():
    mock_db = MockAsyncSession()

    handover_request = EmployeeHandoverRequest(
        id=1,
        from_user_id=10,
        to_user_id=20,
        status=HandoverRequestStatus.PENDING_EXECUTION,
        scope_config={"entities": ["Lead"]},
    )

    from_user = User(id=10, name="离职员工")
    customer = TerminalCustomer(
        id=100,
        customer_code="C001",
        customer_name="客户",
        credit_code="123456789012345678",
        customer_industry="IT",
        customer_region="上海",
        customer_owner_id=10,
        customer_status="active",
    )
    lead = Lead(
        id=200,
        lead_code="L001",
        lead_name="线索",
        terminal_customer_id=100,
        sales_owner_id=10,
        notes="",
    )

    mock_db.queue_result([from_user])
    mock_db.queue_result([lead])
    for _ in range(7):
        mock_db.queue_result([])

    service = HandoverService(mock_db)
    result = await service.execute_handover(handover_request)

    assert result["success"] is True
    assert lead.sales_owner_id == 20
    assert customer.customer_owner_id == 10
    assert "TerminalCustomer" in result["execution_summary"]["skipped"]


async def test_handover_execute_idempotent():
    mock_db = MockAsyncSession()

    handover_request = EmployeeHandoverRequest(
        id=1, from_user_id=10, to_user_id=20,
        status=HandoverRequestStatus.COMPLETED
    )

    service = HandoverService(mock_db)
    result = await service.execute_handover(handover_request)

    assert result["success"] is True
    assert result["already_completed"] is True


async def test_handover_cancel_blocks_completed():
    mock_db = MockAsyncSession()

    handover_request = EmployeeHandoverRequest(
        id=1, from_user_id=10, to_user_id=20,
        status=HandoverRequestStatus.COMPLETED
    )

    service = HandoverService(mock_db)

    with pytest.raises(ValueError, match="已完成的交接不能取消"):
        await service.cancel_handover(handover_request)


async def test_handover_cancel_pending():
    mock_db = MockAsyncSession()

    handover_request = EmployeeHandoverRequest(
        id=1, from_user_id=10, to_user_id=None,
        status=HandoverRequestStatus.PENDING_ASSIGNMENT
    )

    service = HandoverService(mock_db)
    result = await service.cancel_handover(handover_request, "reason")

    assert result.status == HandoverRequestStatus.CANCELED
    assert result.error_message == "reason"
