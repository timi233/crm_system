"""Tests for notification center."""
import pytest
from datetime import datetime

from app.models.notification import Notification
from app.services.notification_service import NotificationService


pytestmark = pytest.mark.asyncio


class MockResult:
    def __init__(self, items):
        self._items = list(items)

    def scalars(self):
        return self

    def all(self):
        return self._items

    def scalar(self):
        return self._items[0] if self._items else 0

    def scalar_one_or_none(self):
        return self._items[0] if self._items else None


class MockDB:
    def __init__(self):
        self._stored = {}
        self._queued_results = []
        self._id_counter = 1

    def queue_result(self, items):
        self._queued_results.append(items)

    async def execute(self, query):
        if self._queued_results:
            return MockResult(self._queued_results.pop(0))
        return MockResult([])

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

    async def refresh(self, obj, attrs=None):
        return None


async def test_create_notification():
    mock_db = MockDB()
    service = NotificationService(mock_db)

    n = await service.create(
        user_id=1,
        notification_type="test",
        title="Test",
        content="Content",
        entity_type="work_report",
        entity_id=5,
    )

    assert n.id == 1
    assert n.title == "Test"
    assert n.entity_id == 5
    assert len(mock_db._stored["Notification"]) == 1


async def test_list_user_notifications():
    mock_db = MockDB()
    mock_db.queue_result([
        Notification(id=1, user_id=1, notification_type="test", title="A", content="c", created_at=datetime.utcnow()),
        Notification(id=2, user_id=1, notification_type="test", title="B", content="c", created_at=datetime.utcnow()),
    ])

    service = NotificationService(mock_db)
    items = await service.list_user_notifications(1, limit=10)

    assert len(items) == 2
    assert items[0].title == "A"


async def test_list_notifications_filters_unread():
    mock_db = MockDB()
    mock_db.queue_result([
        Notification(id=1, user_id=1, notification_type="test", title="Unread", content="c", is_read=False, created_at=datetime.utcnow()),
    ])

    service = NotificationService(mock_db)
    items = await service.list_user_notifications(1, is_read=False, limit=10)

    assert len(items) == 1


async def test_count_unread():
    mock_db = MockDB()
    mock_db.queue_result([5])

    service = NotificationService(mock_db)
    count = await service.count_unread(1)
    assert count == 5


async def test_count_user_notifications_with_filters():
    mock_db = MockDB()
    mock_db.queue_result([10])

    service = NotificationService(mock_db)
    count = await service.count_user_notifications(1, is_read=False, notification_type="work_report_comment")
    assert count == 10


async def test_count_user_notifications_total():
    mock_db = MockDB()
    mock_db.queue_result([25])

    service = NotificationService(mock_db)
    count = await service.count_user_notifications(1)
    assert count == 25


async def test_mark_read():
    mock_db = MockDB()
    n = Notification(id=1, user_id=1, notification_type="test", title="Test", content="c", is_read=False, created_at=datetime.utcnow())
    mock_db._stored.setdefault("Notification", []).append(n)
    mock_db.queue_result([n])

    service = NotificationService(mock_db)
    result = await service.mark_read(1, 1)

    assert result is not None
    assert result.is_read is True


async def test_mark_read_denies_other_user():
    mock_db = MockDB()
    mock_db.queue_result([])

    service = NotificationService(mock_db)
    result = await service.mark_read(1, 2)
    assert result is None


async def test_mark_all_read():
    mock_db = MockDB()
    n1 = Notification(id=1, user_id=1, notification_type="test", title="A", content="c", is_read=False, created_at=datetime.utcnow())
    n2 = Notification(id=2, user_id=1, notification_type="test", title="B", content="c", is_read=False, created_at=datetime.utcnow())
    mock_db.queue_result([n1, n2])

    service = NotificationService(mock_db)
    count = await service.mark_all_read(1)

    assert count == 2
    assert n1.is_read is True
    assert n2.is_read is True


async def test_create_notification_rollback_on_error():
    mock_db = MockDB()

    async def failing_commit():
        raise RuntimeError("DB error")

    mock_db.commit = failing_commit

    service = NotificationService(mock_db)

    with pytest.raises(RuntimeError, match="DB error"):
        await service.create(user_id=1, notification_type="test", title="T", content="C")

    assert mock_db._stored["Notification"][0].id == 1
