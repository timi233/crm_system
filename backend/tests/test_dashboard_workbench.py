import pytest

pytestmark = pytest.mark.asyncio


async def test_workbench_requires_auth(client):
    response = await client.get("/dashboard/workbench")
    assert response.status_code == 401


async def test_workbench_admin_returns_200(client, auth_as, admin_user, fake_db):
    auth_as(admin_user)
    fake_db.queue_result(rows=[(0,)])
    fake_db.queue_result(rows=[(0,)])
    fake_db.queue_result(rows=[(0,)])
    fake_db.queue_result(rows=[(0,)])
    fake_db.queue_result(rows=[(0,)])
    fake_db.queue_result(items=[])

    response = await client.get("/dashboard/workbench")
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "admin"
    assert data["scope"] == "global"
    assert "metrics" in data
    assert "quick_actions" in data
    assert len(data["quick_actions"]) >= 3


async def test_workbench_business_returns_200(client, auth_as, business_user, fake_db):
    auth_as(business_user)
    fake_db.queue_result(rows=[(0,)])
    fake_db.queue_result(rows=[(0,)])
    fake_db.queue_result(rows=[(0,)])
    fake_db.queue_result(rows=[(0,)])
    fake_db.queue_result(rows=[(0,)])
    fake_db.queue_result(items=[])
    fake_db.queue_result(rows=[(0,)])

    response = await client.get("/dashboard/workbench")
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "business"
    assert data["scope"] == "team"
    assert "metrics" in data
    assert "report_status" in data


async def test_workbench_sales_returns_200(client, auth_as, sales_user, fake_db):
    auth_as(sales_user)
    fake_db.queue_result(rows=[(0,)])
    fake_db.queue_result(rows=[(0,)])
    fake_db.queue_result(rows=[(0,)])
    fake_db.queue_result(rows=[(0,)])
    fake_db.queue_result(rows=[(0,)])
    fake_db.queue_result(items=[])
    fake_db.queue_result(items=[])

    response = await client.get("/dashboard/workbench")
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "sales"
    assert data["scope"] == "personal"
    assert "metrics" in data
    assert "report_status" in data
    assert data["report_status"]["daily"] in ("not_created", "draft", "submitted", "withdrawn")


async def test_workbench_finance_returns_200(client, auth_as, finance_user, fake_db):
    auth_as(finance_user)
    fake_db.queue_result(rows=[(0,)])
    fake_db.queue_result(rows=[(0,)])

    response = await client.get("/dashboard/workbench")
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "finance"
    assert data["scope"] == "global"
    assert "metrics" in data
    assert "report_status" not in data or data["report_status"] is None
    assert len(data["quick_actions"]) >= 2


async def test_workbench_finance_no_report_todos(client, auth_as, finance_user, fake_db):
    auth_as(finance_user)
    fake_db.queue_result(rows=[(0,)])
    fake_db.queue_result(rows=[(0,)])

    response = await client.get("/dashboard/workbench")
    assert response.status_code == 200
    data = response.json()
    has_report_action = any(
        "report" in action.get("key", "") or "日报" in action.get("title", "")
        for action in data.get("quick_actions", [])
    )
    assert not has_report_action
    has_report_todo = any(
        "report" in todo.get("key", "") or "日报" in todo.get("title", "") or "周报" in todo.get("title", "")
        for todo in data.get("todos", [])
    )
    assert not has_report_todo


async def test_workbench_technician_returns_200(client, auth_as, technician_user, fake_db):
    auth_as(technician_user)
    fake_db.queue_result(rows=[(0,)])
    fake_db.queue_result(rows=[(0,)])
    fake_db.queue_result(items=[])
    fake_db.queue_result(items=[])

    response = await client.get("/dashboard/workbench")
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "technician"
    assert data["scope"] == "personal"
    assert "metrics" in data
    assert any(m["key"] in ("assigned", "pending", "in_progress") for m in data["metrics"])
    assert "report_status" in data


async def test_workbench_channel_ops_returns_200(client, auth_as, channel_ops_user, fake_db):
    auth_as(channel_ops_user)
    fake_db.queue_result(rows=[(0,)])
    fake_db.queue_result(rows=[(0,)])
    fake_db.queue_result(rows=[(0,)])
    fake_db.queue_result(items=[])

    response = await client.get("/dashboard/workbench")
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "channel_ops"
    assert data["scope"] == "personal"
    assert "metrics" in data
    assert any(m["key"] in ("channels", "followups", "plans") for m in data["metrics"])
    assert "report_status" in data


async def test_workbench_sales_has_report_status(client, auth_as, sales_user, fake_db):
    auth_as(sales_user)
    fake_db.queue_result(rows=[(0,)])
    fake_db.queue_result(rows=[(0,)])
    fake_db.queue_result(rows=[(0,)])
    fake_db.queue_result(rows=[(0,)])
    fake_db.queue_result(rows=[(0,)])
    fake_db.queue_result(items=[])
    fake_db.queue_result(items=[])

    response = await client.get("/dashboard/workbench")
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "sales"
    assert "report_status" in data
    assert "daily" in data["report_status"]
    assert "weekly" in data["report_status"]


async def test_workbench_structure_complete(client, auth_as, admin_user, fake_db):
    auth_as(admin_user)
    fake_db.queue_result(rows=[(0,)])
    fake_db.queue_result(rows=[(0,)])
    fake_db.queue_result(rows=[(0,)])
    fake_db.queue_result(rows=[(0,)])
    fake_db.queue_result(rows=[(0,)])
    fake_db.queue_result(items=[])

    response = await client.get("/dashboard/workbench")
    assert response.status_code == 200
    data = response.json()

    assert "role" in data
    assert "scope" in data
    assert "metrics" in data
    assert isinstance(data["metrics"], list)
    assert "todos" in data
    assert isinstance(data["todos"], list)
    assert "risks" in data
    assert isinstance(data["risks"], list)
    assert "quick_actions" in data
    assert isinstance(data["quick_actions"], list)
    assert "generated_at" in data

    if data["metrics"]:
        metric = data["metrics"][0]
        assert "key" in metric
        assert "title" in metric
        assert "value" in metric

    if data["quick_actions"]:
        action = data["quick_actions"][0]
        assert "key" in action
        assert "title" in action
        assert "link" in action


async def test_workbench_business_team_report_status_format(client, auth_as, business_user, fake_db):
    auth_as(business_user)
    fake_db.queue_result(rows=[(0,)])
    fake_db.queue_result(rows=[(0,)])
    fake_db.queue_result(rows=[(0,)])
    fake_db.queue_result(rows=[(0,)])
    fake_db.queue_result(rows=[(0,)])
    fake_db.queue_result(items=[])
    fake_db.queue_result(rows=[(0,)])

    response = await client.get("/dashboard/workbench")
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "business"
    assert "report_status" in data
    daily_status = data["report_status"]["daily"]
    weekly_status = data["report_status"]["weekly"]
    assert "已提交" in daily_status or daily_status == "0/0 已提交"
    assert "已提交" in weekly_status or weekly_status == "0/0 已提交"


async def test_workbench_sales_unsubmitted_daily_report_todo(client, auth_as, sales_user, fake_db):
    auth_as(sales_user)
    fake_db.queue_result(rows=[(0,)])
    fake_db.queue_result(rows=[(0,)])
    fake_db.queue_result(rows=[(0,)])
    fake_db.queue_result(rows=[(0,)])
    fake_db.queue_result(rows=[(0,)])
    fake_db.queue_result(items=[])
    fake_db.queue_result(items=[])

    response = await client.get("/dashboard/workbench")
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "sales"
    if data["report_status"]["daily"] == "not_created":
        has_daily_todo = any(
            todo.get("key") == "daily_report_missing"
            for todo in data.get("todos", [])
        )
        assert has_daily_todo


async def test_workbench_channel_ops_unsubmitted_daily_report_todo(client, auth_as, channel_ops_user, fake_db):
    auth_as(channel_ops_user)
    fake_db.queue_result(rows=[(0,)])
    fake_db.queue_result(rows=[(0,)])
    fake_db.queue_result(rows=[(0,)])
    fake_db.queue_result(items=[])

    response = await client.get("/dashboard/workbench")
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "channel_ops"
    if data["report_status"]["daily"] == "not_created":
        has_daily_todo = any(
            todo.get("key") == "daily_report_missing"
            for todo in data.get("todos", [])
        )
        assert has_daily_todo


async def test_workbench_department_manager_report_status(client, auth_as, sales_user, fake_db):
    auth_as(sales_user)
    fake_db.queue_result(rows=[(0,)])  # current user lookup
    fake_db.queue_result(rows=[(0,)])  # leads count
    fake_db.queue_result(rows=[(0,)])  # opportunities count
    fake_db.queue_result(rows=[(0,)])  # targets count
    fake_db.queue_result(rows=[(0,)])  # followups count
    fake_db.queue_result(items=[])  # pending followups
    fake_db.queue_result(items=[])  # personal daily report
    fake_db.queue_result(items=[])  # personal weekly report
    fake_db.queue_result(items=[object()])  # has at least one direct member
    fake_db.queue_result(rows=[(6,), (7,)])  # direct member ids
    fake_db.queue_result(rows=[(1,)])  # daily submitted count
    fake_db.queue_result(rows=[(0,)])  # weekly submitted count

    response = await client.get("/dashboard/workbench")

    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "sales"
    assert data["scope"] == "team"
    assert data["report_status"]["daily"] == "1/2 已提交"
    assert data["report_status"]["weekly"] == "0/2 已提交"
