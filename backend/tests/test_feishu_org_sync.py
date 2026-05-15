import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import itertools

from app.services.feishu_org_sync_service import FeishuOrgSyncService
from app.services.feishu_service import FeishuAPIError
from app.models.user import User, FeishuEmploymentStatus
from app.models.feishu_org_sync_run import FeishuOrgSyncRun


pytestmark = pytest.mark.asyncio


class MockAsyncSession:
    """Mock database session for testing."""
    def __init__(self):
        self.users = []
        self.sync_runs = []
        self._id_counter = itertools.count(1)
        self._queued_results = []

    def queue_result(self, items):
        self._queued_results.append(items)

    async def execute(self, query):
        if self._queued_results:
            return MockScalarResult(self._queued_results.pop(0))
        return MockScalarResult([])

    def add(self, obj):
        if getattr(obj, "id", None) is None:
            setattr(obj, "id", next(self._id_counter))
        model_type = type(obj).__name__
        if model_type == "User":
            self.users.append(obj)
        elif model_type == "FeishuOrgSyncRun":
            self.sync_runs.append(obj)
        else:
            setattr(self, model_type, getattr(self, model_type, []))
            getattr(self, model_type).append(obj)

    async def commit(self):
        return None

    async def rollback(self):
        return None

    async def flush(self):
        return None

    async def refresh(self, obj, attrs=None):
        return None


class MockScalarResult:
    """Mock scalar result from execute."""
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


async def test_sync_users_creates_new_user():
    """Test that sync creates new user with correct defaults."""
    mock_db = MockAsyncSession()

    mock_departments = [
        {"open_department_id": "dept_root", "name": "Root Department", "parent_department_id": "0"},
        {"open_department_id": "dept_1", "name": "Department 1", "parent_department_id": "dept_root"},
    ]
    mock_members = [
        {
            "open_id": "ou_test123",
            "union_id": "on_union123",
            "name": "Test User",
            "email": "test@example.com",
            "mobile": "13800138000",
            "avatar": {"avatar_origin": "https://example.com/avatar.jpg"},
            "department_ids": ["dept_1"],
        }
    ]

    with patch("app.services.feishu_org_sync_service.feishu_service") as mock_feishu:
        mock_feishu.get_departments = AsyncMock(return_value=mock_departments)
        mock_feishu.get_department_members = AsyncMock(return_value=mock_members)

        mock_db.queue_result([])

        sync_service = FeishuOrgSyncService(mock_db)
        result = await sync_service.sync_users()

    assert result["created"] == 1
    assert result["updated"] == 0
    assert result["errors"] == 0
    assert len(mock_db.users) == 1

    new_user = mock_db.users[0]
    assert new_user.feishu_id == "ou_test123"
    assert new_user.feishu_union_id == "on_union123"
    assert new_user.name == "Test User"
    assert new_user.email == "test@example.com"
    assert new_user.phone == "13800138000"
    assert new_user.department == "Root Department / Department 1"
    assert new_user.is_active is True
    assert new_user.role == "sales"
    assert new_user.hashed_password is None


async def test_sync_users_new_user_default_active_sales():
    """New synced users are enabled by default and role=sales."""
    mock_db = MockAsyncSession()

    mock_departments = [{"open_department_id": "dept_1", "name": "Sales"}]
    mock_members = [
        {
            "open_id": "ou_new_user",
            "name": "New User",
            "email": "new@example.com",
        }
    ]

    with patch("app.services.feishu_org_sync_service.feishu_service") as mock_feishu:
        mock_feishu.get_departments = AsyncMock(return_value=mock_departments)
        mock_feishu.get_department_members = AsyncMock(return_value=mock_members)

        mock_db.queue_result([])

        sync_service = FeishuOrgSyncService(mock_db)
        await sync_service.sync_users()

    assert len(mock_db.users) == 1
    user = mock_db.users[0]
    assert user.is_active is True
    assert user.role == "sales"
    assert user.hashed_password is None


async def test_sync_users_existing_user_not_overwritten():
    """Existing user should not have role/is_active overwritten."""
    mock_db = MockAsyncSession()

    # Pre-existing user with admin role and active
    existing_user = User(
        id=100,
        feishu_id="ou_existing",
        name="Existing Admin",
        email="admin@example.com",
        is_active=True,
        role="admin",
        hashed_password="hashed123",
    )
    mock_db.users.append(existing_user)

    mock_departments = [{"open_department_id": "dept_1", "name": "Admin Department"}]
    mock_members = [
        {
            "open_id": "ou_existing",
            "union_id": "on_union_existing",
            "name": "Existing Admin Updated",
            "email": "admin@example.com",
            "mobile": "13900139000",
            "department_ids": ["dept_1"],
        }
    ]

    with patch("app.services.feishu_org_sync_service.feishu_service") as mock_feishu:
        mock_feishu.get_departments = AsyncMock(return_value=mock_departments)
        mock_feishu.get_department_members = AsyncMock(return_value=mock_members)

        sync_service = FeishuOrgSyncService(mock_db)
        # Queue the existing user for lookup
        mock_db.queue_result([existing_user])
        result = await sync_service.sync_users()

    assert result["updated"] == 1
    assert result["created"] == 0

    # Role and is_active should not be changed
    assert existing_user.role == "admin"
    assert existing_user.is_active is True
    assert existing_user.hashed_password == "hashed123"

    # But feishu fields should be updated
    assert existing_user.feishu_union_id == "on_union_existing"
    assert existing_user.name == "Existing Admin Updated"
    assert existing_user.phone == "13900139000"
    assert existing_user.department == "Admin Department"


async def test_sync_users_match_priority_open_id_first():
    """Match priority: open_id > union_id > email > phone."""
    mock_db = MockAsyncSession()

    # User with open_id
    user_by_open_id = User(
        id=1,
        feishu_id="ou_match_open",
        name="User Open",
        email="open@example.com",
    )
    # User with union_id
    user_by_union_id = User(
        id=2,
        feishu_union_id="on_match_union",
        name="User Union",
        email="union@example.com",
    )
    # User with email
    user_by_email = User(
        id=3,
        email="email@example.com",
        name="User Email",
    )
    # User with phone
    user_by_phone = User(
        id=4,
        phone="13800138001",
        name="User Phone",
    )

    mock_db.users = [user_by_open_id, user_by_union_id, user_by_email, user_by_phone]

    mock_departments = [{"open_department_id": "dept_1"}]

    # Member matches by open_id first
    mock_members = [
        {
            "open_id": "ou_match_open",
            "union_id": "on_other",
            "email": "other@example.com",
            "mobile": "13900139000",
            "name": "Should Match Open ID",
        }
    ]

    with patch("app.services.feishu_org_sync_service.feishu_service") as mock_feishu:
        mock_feishu.get_departments = AsyncMock(return_value=mock_departments)
        mock_feishu.get_department_members = AsyncMock(return_value=mock_members)

        sync_service = FeishuOrgSyncService(mock_db)
        mock_db.queue_result([user_by_open_id])
        result = await sync_service.sync_users()

    assert result["updated"] == 1
    assert result["created"] == 0
    assert user_by_open_id.name == "Should Match Open ID"


async def test_sync_users_match_priority_union_id_second():
    """If open_id not found, match by union_id."""
    mock_db = MockAsyncSession()

    user_by_union_id = User(
        id=2,
        feishu_union_id="on_match_union",
        name="User Union",
        email="union@example.com",
    )

    mock_db.users = [user_by_union_id]

    mock_departments = [{"open_department_id": "dept_1"}]
    mock_members = [
        {
            "open_id": "ou_not_exist",
            "union_id": "on_match_union",
            "email": "other@example.com",
            "name": "Should Match Union ID",
        }
    ]

    with patch("app.services.feishu_org_sync_service.feishu_service") as mock_feishu:
        mock_feishu.get_departments = AsyncMock(return_value=mock_departments)
        mock_feishu.get_department_members = AsyncMock(return_value=mock_members)

        sync_service = FeishuOrgSyncService(mock_db)
        # First lookup (open_id) returns None
        mock_db.queue_result([])
        # Second lookup (union_id) returns user
        mock_db.queue_result([user_by_union_id])
        result = await sync_service.sync_users()

    assert result["updated"] == 1
    assert user_by_union_id.feishu_id == "ou_not_exist"
    assert user_by_union_id.name == "Should Match Union ID"


async def test_sync_users_match_priority_email_third():
    """If open_id and union_id not found, match by email."""
    mock_db = MockAsyncSession()

    user_by_email = User(
        id=3,
        email="email@example.com",
        name="User Email",
    )

    mock_db.users = [user_by_email]

    mock_departments = [{"open_department_id": "dept_1"}]
    mock_members = [
        {
            "open_id": "ou_not_exist",
            "union_id": "on_not_exist",
            "email": "email@example.com",
            "name": "Should Match Email",
        }
    ]

    with patch("app.services.feishu_org_sync_service.feishu_service") as mock_feishu:
        mock_feishu.get_departments = AsyncMock(return_value=mock_departments)
        mock_feishu.get_department_members = AsyncMock(return_value=mock_members)

        sync_service = FeishuOrgSyncService(mock_db)
        mock_db.queue_result([])  # open_id lookup
        mock_db.queue_result([])  # union_id lookup
        mock_db.queue_result([user_by_email])  # email lookup
        result = await sync_service.sync_users()

    assert result["updated"] == 1
    assert user_by_email.feishu_id == "ou_not_exist"
    assert user_by_email.name == "Should Match Email"


async def test_sync_users_match_priority_phone_fourth():
    """If open_id, union_id, email not found, match by phone."""
    mock_db = MockAsyncSession()

    user_by_phone = User(
        id=4,
        phone="13800138001",
        name="User Phone",
    )

    mock_db.users = [user_by_phone]

    mock_departments = [{"open_department_id": "dept_1"}]
    mock_members = [
        {
            "open_id": "ou_not_exist",
            "union_id": "on_not_exist",
            "email": "other@example.com",
            "mobile": "13800138001",
            "name": "Should Match Phone",
        }
    ]

    with patch("app.services.feishu_org_sync_service.feishu_service") as mock_feishu:
        mock_feishu.get_departments = AsyncMock(return_value=mock_departments)
        mock_feishu.get_department_members = AsyncMock(return_value=mock_members)

        sync_service = FeishuOrgSyncService(mock_db)
        mock_db.queue_result([])  # open_id lookup
        mock_db.queue_result([])  # union_id lookup
        mock_db.queue_result([])  # email lookup
        mock_db.queue_result([user_by_phone])  # phone lookup
        result = await sync_service.sync_users()

    assert result["updated"] == 1
    assert user_by_phone.feishu_id == "ou_not_exist"
    assert user_by_phone.name == "Should Match Phone"


async def test_sync_users_pagination():
    """Feishu API pagination should be handled correctly."""
    mock_db = MockAsyncSession()

    mock_departments = [{"open_department_id": "dept_1"}]

    with patch("app.services.feishu_org_sync_service.feishu_service") as mock_feishu:
        mock_feishu.get_departments = AsyncMock(return_value=mock_departments)
        mock_feishu.get_department_members = AsyncMock(
            return_value=[
                {"open_id": "ou_1", "name": "User 1"},
                {"open_id": "ou_2", "name": "User 2"},
            ]
        )

        mock_db.queue_result([])

        sync_service = FeishuOrgSyncService(mock_db)
        result = await sync_service.sync_users()

    assert result["created"] == 2
    assert len(mock_db.users) == 2


async def test_sync_users_single_member_error_not_breaks_batch():
    """Single member exception should not interrupt batch sync."""
    mock_db = MockAsyncSession()

    mock_departments = [{"open_department_id": "dept_1"}]

    # One good member, one bad member (no open_id to trigger error)
    mock_members = [
        {
            "open_id": "ou_good",
            "name": "Good User",
            "email": "good@example.com",
        },
        {
            # Missing open_id will cause sync to work but with empty feishu_id
            "name": "Bad User",
        },
        {
            "open_id": "ou_good2",
            "name": "Good User 2",
        },
    ]

    with patch("app.services.feishu_org_sync_service.feishu_service") as mock_feishu:
        mock_feishu.get_departments = AsyncMock(return_value=mock_departments)
        mock_feishu.get_department_members = AsyncMock(return_value=mock_members)

        sync_service = FeishuOrgSyncService(mock_db)
        result = await sync_service.sync_users()

    # Should create users, potentially one error for bad data
    assert result["created"] >= 2
    assert len(mock_db.users) >= 2


async def test_sync_users_department_error_recorded():
    """Department fetch error should be recorded in error_details."""
    mock_db = MockAsyncSession()

    with patch("app.services.feishu_org_sync_service.feishu_service") as mock_feishu:
        mock_feishu.get_departments = AsyncMock(
            side_effect=FeishuAPIError(1001, "Permission denied")
        )

        sync_service = FeishuOrgSyncService(mock_db)
        result = await sync_service.sync_users()

    assert result["errors"] == 1
    assert len(result["error_details"]) == 1
    assert result["error_details"][0]["type"] == "departments"


async def test_departure_detection_uses_union_id_seen_key():
    """Users with only union_id should not be marked left when union_id is seen."""
    mock_db = MockAsyncSession()
    sync_service = FeishuOrgSyncService(mock_db)
    previous_run = FeishuOrgSyncRun(id=1, status="success")
    current_run = FeishuOrgSyncRun(id=2, status="running")
    user = User(
        id=10,
        name="Union User",
        feishu_union_id="on_seen",
        feishu_employment_status=FeishuEmploymentStatus.ACTIVE,
        is_active=True,
        feishu_last_sync_run_id=1,
    )

    mock_db.queue_result([previous_run])
    mock_db.queue_result([user])

    result = await sync_service._detect_departures({"union:on_seen"}, current_run)

    assert result["left_detected"] == 0
    assert user.is_active is True
    assert user.feishu_employment_status == FeishuEmploymentStatus.ACTIVE


async def test_departure_detection_creates_handover_and_notification_for_manager():
    """Departed users are disabled and assigned to direct manager."""
    mock_db = MockAsyncSession()
    sync_service = FeishuOrgSyncService(mock_db)
    previous_run = FeishuOrgSyncRun(id=1, status="success")
    current_run = FeishuOrgSyncRun(id=2, status="running")
    manager = User(id=20, name="Manager", role="business", is_active=True)
    user = User(
        id=10,
        name="Departed User",
        feishu_id="ou_left",
        department_manager_id=20,
        feishu_employment_status=FeishuEmploymentStatus.ACTIVE,
        is_active=True,
        feishu_last_sync_run_id=1,
    )
    active_users = [user]
    seen_keys = set()
    for index in range(19):
        active_user = User(
            id=100 + index,
            name=f"Active User {index}",
            feishu_id=f"ou_seen_{index}",
            feishu_employment_status=FeishuEmploymentStatus.ACTIVE,
            is_active=True,
            feishu_last_sync_run_id=1,
        )
        active_users.append(active_user)
        seen_keys.add(f"open:{active_user.feishu_id}")

    mock_db.queue_result([previous_run])
    mock_db.queue_result(active_users)
    mock_db.queue_result([manager])

    result = await sync_service._detect_departures(seen_keys, current_run)

    assert result["left_detected"] == 1
    assert user.is_active is False
    assert user.feishu_employment_status == FeishuEmploymentStatus.PENDING_HANDOVER
    assert user.feishu_last_sync_run_id == 2
    requests = getattr(mock_db, "EmployeeHandoverRequest")
    notifications = getattr(mock_db, "Notification")
    assert requests[0].from_user_id == 10
    assert requests[0].team_manager_user_id == 20
    assert notifications[0].user_id == 20
    assert notifications[0].entity_id == requests[0].id


async def test_sync_users_stores_full_department_path_for_duplicate_names():
    """Department paths disambiguate duplicate leaf department names."""
    mock_db = MockAsyncSession()

    mock_departments = [
        {"open_department_id": "tech", "name": "技术部", "parent_department_id": "0"},
        {"open_department_id": "tech_ipg", "name": "IPG", "parent_department_id": "tech"},
        {"open_department_id": "sales", "name": "销售部", "parent_department_id": "0"},
        {"open_department_id": "sales_ipg", "name": "IPG", "parent_department_id": "sales"},
    ]
    mock_members_by_dept = {
        "tech": [],
        "tech_ipg": [
            {"open_id": "ou_tech", "name": "Tech User", "department_ids": ["tech_ipg"]}
        ],
        "sales": [],
        "sales_ipg": [
            {"open_id": "ou_sales", "name": "Sales User", "department_ids": ["sales_ipg"]}
        ],
    }

    with patch("app.services.feishu_org_sync_service.feishu_service") as mock_feishu:
        mock_feishu.get_departments = AsyncMock(return_value=mock_departments)
        mock_feishu.get_department_members = AsyncMock(
            side_effect=lambda dept_id: mock_members_by_dept[dept_id]
        )

        mock_db.queue_result([])

        sync_service = FeishuOrgSyncService(mock_db)
        result = await sync_service.sync_users()

    assert result["created"] == 2
    departments = {user.name: user.department for user in mock_db.users}
    assert departments["Tech User"] == "技术部 / IPG"
    assert departments["Sales User"] == "销售部 / IPG"


async def test_preview_sync_users():
    """Preview should return user mapping info without creating users."""
    mock_db = MockAsyncSession()

    existing_user = User(
        id=100,
        feishu_id="ou_existing",
        name="Existing User",
        email="existing@example.com",
    )
    mock_db.users.append(existing_user)

    mock_departments = [{"open_department_id": "dept_1"}]
    mock_members = [
        {
            "open_id": "ou_existing",
            "name": "Existing User",
            "email": "existing@example.com",
            "department_ids": ["dept_1"],
        },
        {
            "open_id": "ou_new",
            "name": "New User",
            "email": "new@example.com",
            "department_ids": ["dept_1"],
        },
    ]

    with patch("app.services.feishu_org_sync_service.feishu_service") as mock_feishu:
        mock_feishu.get_departments = AsyncMock(return_value=mock_departments)
        mock_feishu.get_department_members = AsyncMock(return_value=mock_members)

        sync_service = FeishuOrgSyncService(mock_db)
        mock_db.queue_result([existing_user])  # first user lookup
        mock_db.queue_result([])  # second user lookup (new user)
        result = await sync_service.preview_sync_users()

    assert result["total_members"] == 2
    assert len(result["preview_users"]) == 2

    # Existing user
    existing_preview = result["preview_users"][0]
    assert existing_preview["crm_user_id"] == 100
    assert existing_preview["will_create"] is False
    assert existing_preview["feishu_department"] == "dept_1"

    # New user
    new_preview = result["preview_users"][1]
    assert new_preview["crm_user_id"] is None
    assert new_preview["will_create"] is True
    assert new_preview["feishu_department"] == "dept_1"


async def test_sync_users_endpoint_requires_admin(client, auth_as, sales_user, fake_db):
    """sync-users endpoint requires admin role."""
    auth_as(sales_user)
    response = await client.post("/integrations/feishu/sync-users")
    assert response.status_code == 403


async def test_sync_preview_endpoint_requires_admin(client, auth_as, sales_user, fake_db):
    """sync-preview endpoint requires admin role."""
    auth_as(sales_user)
    response = await client.get("/integrations/feishu/sync-preview")
    assert response.status_code == 403


async def test_sync_users_endpoint_admin_ok(client, auth_as, admin_user, fake_db):
    """sync-users endpoint accessible by admin."""
    auth_as(admin_user)

    with patch("app.services.feishu_org_sync_service.feishu_service") as mock_feishu:
        mock_feishu.get_departments = AsyncMock(return_value=[])
        mock_feishu.get_department_members = AsyncMock(return_value=[])

        response = await client.post("/integrations/feishu/sync-users")

    assert response.status_code == 200
    data = response.json()
    assert "created" in data
    assert "updated" in data
    assert "errors" in data


async def test_sync_preview_endpoint_admin_ok(client, auth_as, admin_user, fake_db):
    """sync-preview endpoint accessible by admin."""
    auth_as(admin_user)

    with patch("app.services.feishu_org_sync_service.feishu_service") as mock_feishu:
        mock_feishu.get_departments = AsyncMock(return_value=[])
        mock_feishu.get_department_members = AsyncMock(return_value=[])

        response = await client.get("/integrations/feishu/sync-preview")

    assert response.status_code == 200
    data = response.json()
    assert "total_members" in data
    assert "preview_users" in data
