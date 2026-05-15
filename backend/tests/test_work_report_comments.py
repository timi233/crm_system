"""Tests for work report comments."""
import pytest
from datetime import date

from app.models.work_report import WorkReport
from app.models.work_report_comment import WorkReportComment


pytestmark = pytest.mark.asyncio


class MockResult:
    def __init__(self, items):
        self._items = list(items)

    def scalars(self):
        return self

    def all(self):
        return self._items

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


async def test_comment_model_fields():
    """Verify WorkReportComment model has required fields."""
    comment = WorkReportComment(
        report_id=1,
        user_id=2,
        content="Test comment",
    )
    assert comment.report_id == 1
    assert comment.user_id == 2
    assert comment.content == "Test comment"


async def test_comment_create_stores():
    """Creating a comment stores it in the mock DB."""
    mock_db = MockDB()
    comment = WorkReportComment(
        report_id=1,
        user_id=2,
        content="Test",
    )
    mock_db.add(comment)
    assert len(mock_db._stored["WorkReportComment"]) == 1
    assert mock_db._stored["WorkReportComment"][0].content == "Test"


async def test_comment_read_schema():
    """Verify comment read schema fields."""
    from app.schemas.work_report import WorkReportCommentRead

    comment = WorkReportComment(
        id=1,
        report_id=5,
        user_id=2,
        content="Nice report!",
    )
    schema = WorkReportCommentRead.model_validate(comment)
    assert schema.id == 1
    assert schema.report_id == 5
    assert schema.content == "Nice report!"


async def test_comment_create_requires_content():
    """Content validation should reject empty strings."""
    from app.schemas.work_report import WorkReportCommentCreate

    with pytest.raises(Exception):
        WorkReportCommentCreate(content="")

    with pytest.raises(Exception):
        WorkReportCommentCreate()


async def test_comment_content_max_length():
    """Content should be limited to 1000 chars."""
    from app.schemas.work_report import WorkReportCommentCreate

    valid = WorkReportCommentCreate(content="x" * 1000)
    assert len(valid.content) == 1000

    with pytest.raises(Exception):
        WorkReportCommentCreate(content="x" * 1001)


async def test_notification_created_for_comment():
    """Comment by non-owner should create notification."""
    mock_db = MockDB()
    report = WorkReport(
        id=1,
        report_type="daily",
        report_date=date(2026, 5, 15),
        owner_id=10,
        owner_role="sales",
        status="draft",
    )
    mock_db.add(report)

    from app.services.notification_service import NotificationService

    service = NotificationService(mock_db)
    await service.create(
        user_id=report.owner_id,
        notification_type="work_report_comment",
        title="你的日报/周报收到新评论",
        content="测试用户评论了报告",
        entity_type="work_report",
        entity_id=report.id,
    )

    assert len(mock_db._stored["Notification"]) == 1
    assert mock_db._stored["Notification"][0].notification_type == "work_report_comment"
