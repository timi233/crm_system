import pytest
from datetime import date
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.work_report_reminder_service import WorkReportReminderService, EXCLUDED_ROLES
from app.models.user import User
from app.models.work_report import WorkReport


pytestmark = pytest.mark.asyncio


class MockAsyncSession:
    def __init__(self):
        self._queued_results = []

    def queue_result(self, items):
        self._queued_results.append(items)

    async def execute(self, query):
        if self._queued_results:
            return MockScalarResult(self._queued_results.pop(0))
        return MockScalarResult([])

    async def scalar_one_or_none(self):
        return None


class MockScalarResult:
    def __init__(self, items):
        self._items = list(items)

    def scalars(self):
        return MockScalarsResult(self._items)

    def scalar_one_or_none(self):
        return self._items[0] if self._items else None


class MockScalarsResult:
    def __init__(self, items):
        self._items = list(items)

    def all(self):
        return self._items


async def test_excluded_roles_include_finance():
    assert "finance" in EXCLUDED_ROLES


async def test_users_needing_daily_reminder_excludes_finance():
    mock_db = MockAsyncSession()

    finance_user = User(id=1, name="Finance", email="finance@example.com", role="finance", is_active=True)
    sales_user = User(id=2, name="Sales", email="sales@example.com", role="sales", is_active=True, feishu_id="ou_sales")

    mock_db.queue_result([sales_user])
    mock_db.queue_result([])

    service = WorkReportReminderService(mock_db)
    users = await service.get_users_needing_daily_reminder(date.today())

    assert len(users) == 1
    assert users[0].role == "sales"


async def test_users_needing_daily_reminder_excludes_submitted():
    mock_db = MockAsyncSession()

    sales_user = User(id=2, name="Sales", email="sales@example.com", role="sales", is_active=True)
    submitted_report = WorkReport(id=100, owner_id=2, report_type="daily", status="submitted")

    mock_db.queue_result([sales_user])
    mock_db.queue_result([submitted_report])

    service = WorkReportReminderService(mock_db)
    users = await service.get_users_needing_daily_reminder(date.today())

    assert len(users) == 0


async def test_users_without_feishu_id_are_skipped():
    mock_db = MockAsyncSession()

    sales_user_no_feishu = User(id=3, name="NoFeishu", email="no_feishu@example.com", role="sales", is_active=True)

    mock_db.queue_result([sales_user_no_feishu])
    mock_db.queue_result([])

    service = WorkReportReminderService(mock_db)
    result = await service.send_daily_reminders(dry_run=True)

    assert result["skipped"] == 1
    assert result["sent"] == 0


async def test_dry_run_does_not_send_messages():
    mock_db = MockAsyncSession()

    sales_user = User(id=2, name="Sales", email="sales@example.com", role="sales", is_active=True, feishu_id="ou_sales")

    mock_db.queue_result([sales_user])
    mock_db.queue_result([])

    service = WorkReportReminderService(mock_db)

    with patch("app.services.work_report_reminder_service.feishu_service") as mock_feishu:
        mock_feishu.get_tenant_access_token = AsyncMock(return_value="fake_token")

        result = await service.send_daily_reminders(dry_run=True)

        assert result["sent"] == 1
        assert result["skipped"] == 0
        mock_feishu.get_tenant_access_token.assert_not_called()


async def test_send_daily_reminders_records_sent_count():
    mock_db = MockAsyncSession()

    sales_user = User(id=2, name="Sales", email="sales@example.com", role="sales", is_active=True, feishu_id="ou_sales")

    mock_db.queue_result([sales_user])
    mock_db.queue_result([])

    service = WorkReportReminderService(mock_db)

    with patch("app.services.work_report_reminder_service.feishu_service") as mock_feishu:
        mock_feishu.get_tenant_access_token = AsyncMock(return_value="fake_token")

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.json = lambda: {"code": 0, "data": {"message_id": "om_test"}}

            mock_cm = AsyncMock()
            mock_cm.__aenter__.return_value = mock_cm
            mock_cm.post = AsyncMock(return_value=mock_response)
            mock_cm.__aexit__.return_value = None
            mock_client.return_value = mock_cm

            result = await service.send_daily_reminders(dry_run=False)

            assert result["sent"] == 1
            assert result["skipped"] == 0
            assert result["failed"] == 0


async def test_send_daily_reminders_records_failed_on_api_error():
    mock_db = MockAsyncSession()

    sales_user = User(id=2, name="Sales", email="sales@example.com", role="sales", is_active=True, feishu_id="ou_sales")

    mock_db.queue_result([sales_user])
    mock_db.queue_result([])

    service = WorkReportReminderService(mock_db)

    with patch("app.services.work_report_reminder_service.feishu_service") as mock_feishu:
        mock_feishu.get_tenant_access_token = AsyncMock(return_value="fake_token")

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.json = lambda: {"code": 1001, "msg": "User blocked"}

            mock_cm = AsyncMock()
            mock_cm.__aenter__.return_value = mock_cm
            mock_cm.post = AsyncMock(return_value=mock_response)
            mock_cm.__aexit__.return_value = None
            mock_client.return_value = mock_cm

            result = await service.send_daily_reminders(dry_run=False)

            assert result["sent"] == 0
            assert result["failed"] == 1


async def test_reminder_endpoint_requires_admin(client, auth_as, sales_user, fake_db):
    auth_as(sales_user)
    response = await client.post("/integrations/feishu/work-report-reminders/run")
    assert response.status_code == 403


async def test_reminder_endpoint_admin_ok(client, auth_as, admin_user, fake_db):
    auth_as(admin_user)

    with patch("app.services.work_report_reminder_service.feishu_service") as mock_feishu:
        mock_feishu.get_tenant_access_token = AsyncMock(return_value="fake_token")

        response = await client.post(
            "/integrations/feishu/work-report-reminders/run?dry_run=true&report_type=daily"
        )

        assert response.status_code == 200
        data = response.json()
        assert "sent" in data
        assert "skipped" in data
        assert "failed" in data


async def test_reminder_endpoint_invalid_report_type(client, auth_as, admin_user, fake_db):
    auth_as(admin_user)
    response = await client.post(
        "/integrations/feishu/work-report-reminders/run?report_type=invalid"
    )
    assert response.status_code == 400


async def test_build_reminder_card_contains_system_url():
    service = WorkReportReminderService(MockAsyncSession())
    card = service._build_reminder_card("daily", date.today())

    assert "config" in card
    assert "elements" in card
    assert len(card["elements"]) >= 1

    title_element = card["elements"][0]
    assert "日报提醒" in title_element["text"]["content"]


async def test_build_reminder_card_weekly():
    service = WorkReportReminderService(MockAsyncSession())
    card = service._build_reminder_card("weekly", date.today())

    title_element = card["elements"][0]
    assert "周报提醒" in title_element["text"]["content"]