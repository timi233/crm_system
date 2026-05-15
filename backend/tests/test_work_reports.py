import pytest
from datetime import date

pytestmark = pytest.mark.asyncio


async def test_list_work_reports_requires_auth(client):
    response = await client.get("/work-reports/")
    assert response.status_code == 401


async def test_list_work_reports_with_auth_returns_200(client, auth_as, admin_user, fake_db):
    auth_as(admin_user)
    fake_db.queue_result(items=[])
    response = await client.get("/work-reports/")
    assert response.status_code == 200


async def test_create_work_report_as_sales(client, auth_as, sales_user, fake_db):
    auth_as(sales_user)
    from app.models.user import User
    fake_user = User(id=sales_user["id"], name=sales_user["name"], email=sales_user["email"], role=sales_user["role"])
    fake_db.queue_result(items=[fake_user])
    response = await client.post(
        "/work-reports/",
        json={
            "report_type": "daily",
            "report_date": "2026-05-13",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["report_type"] == "daily"
    assert data["status"] == "draft"


async def test_finance_cannot_create_work_report(client, auth_as, finance_user, fake_db):
    auth_as(finance_user)
    from app.models.user import User
    fake_user = User(id=finance_user["id"], name=finance_user["name"], email=finance_user["email"], role=finance_user["role"])
    fake_db.queue_result(items=[fake_user])
    response = await client.post(
        "/work-reports/",
        json={
            "report_type": "daily",
            "report_date": "2026-05-13",
        },
    )
    assert response.status_code == 403


async def test_submit_work_report(client, auth_as, sales_user, fake_db):
    auth_as(sales_user)
    from app.models.user import User
    from app.models.work_report import WorkReport
    fake_user = User(id=sales_user["id"], name=sales_user["name"], email=sales_user["email"], role=sales_user["role"])
    fake_db.queue_result(items=[fake_user])

    create_response = await client.post(
        "/work-reports/",
        json={
            "report_type": "daily",
            "report_date": "2026-05-13",
        },
    )
    assert create_response.status_code == 200
    report_id = create_response.json()["id"]

    fake_report = WorkReport(
        id=report_id,
        report_type="daily",
        report_date=date(2026, 5, 13),
        owner_id=sales_user["id"],
        status="draft",
    )
    fake_db.queue_result(items=[fake_report])

    submit_response = await client.post(f"/work-reports/{report_id}/submit")
    assert submit_response.status_code == 200
    data = submit_response.json()
    assert data["status"] == "submitted"


async def test_withdraw_work_report(client, auth_as, sales_user, fake_db):
    auth_as(sales_user)
    from app.models.user import User
    from app.models.work_report import WorkReport
    fake_user = User(id=sales_user["id"], name=sales_user["name"], email=sales_user["email"], role=sales_user["role"])
    fake_db.queue_result(items=[fake_user])

    create_response = await client.post(
        "/work-reports/",
        json={
            "report_type": "daily",
            "report_date": "2026-05-13",
        },
    )
    assert create_response.status_code == 200
    report_id = create_response.json()["id"]

    fake_report = WorkReport(
        id=report_id,
        report_type="daily",
        report_date=date(2026, 5, 13),
        owner_id=sales_user["id"],
        status="submitted",
    )
    fake_db.queue_result(items=[fake_report])

    withdraw_response = await client.post(f"/work-reports/{report_id}/withdraw")
    assert withdraw_response.status_code == 200
    data = withdraw_response.json()
    assert data["status"] == "withdrawn"


async def test_sales_cannot_view_others_report(client, auth_as, sales_user, another_sales_user, fake_db):
    auth_as(another_sales_user)
    from app.models.user import User
    from app.models.work_report import WorkReport
    fake_user = User(id=another_sales_user["id"], name=another_sales_user["name"], email=another_sales_user["email"], role=another_sales_user["role"])
    fake_db.queue_result(items=[fake_user])

    create_response = await client.post(
        "/work-reports/",
        json={
            "report_type": "daily",
            "report_date": "2026-05-13",
        },
    )
    assert create_response.status_code == 200
    report_id = create_response.json()["id"]

    auth_as(sales_user)
    fake_report = WorkReport(
        id=report_id,
        report_type="daily",
        report_date=date(2026, 5, 13),
        owner_id=another_sales_user["id"],
        status="draft",
    )
    fake_db.queue_result(items=[fake_report])

    get_response = await client.get(f"/work-reports/{report_id}")
    assert get_response.status_code == 403


async def test_admin_can_view_all_reports(client, auth_as, admin_user, sales_user, fake_db):
    auth_as(sales_user)
    from app.models.user import User
    from app.models.work_report import WorkReport
    fake_user = User(id=sales_user["id"], name=sales_user["name"], email=sales_user["email"], role=sales_user["role"])
    fake_db.queue_result(items=[fake_user])

    create_response = await client.post(
        "/work-reports/",
        json={
            "report_type": "daily",
            "report_date": "2026-05-13",
        },
    )
    assert create_response.status_code == 200
    report_id = create_response.json()["id"]

    auth_as(admin_user)
    fake_report = WorkReport(
        id=report_id,
        report_type="daily",
        report_date=date(2026, 5, 13),
        owner_id=sales_user["id"],
        status="draft",
    )
    fake_db.queue_result(items=[fake_report])

    get_response = await client.get(f"/work-reports/{report_id}")
    assert get_response.status_code == 200


async def test_business_can_view_all_reports(client, auth_as, business_user, sales_user, fake_db):
    auth_as(sales_user)
    from app.models.user import User
    from app.models.work_report import WorkReport
    fake_user = User(id=sales_user["id"], name=sales_user["name"], email=sales_user["email"], role=sales_user["role"])
    fake_db.queue_result(items=[fake_user])

    create_response = await client.post(
        "/work-reports/",
        json={
            "report_type": "daily",
            "report_date": "2026-05-13",
        },
    )
    assert create_response.status_code == 200
    report_id = create_response.json()["id"]

    auth_as(business_user)
    fake_report = WorkReport(
        id=report_id,
        report_type="daily",
        report_date=date(2026, 5, 13),
        owner_id=sales_user["id"],
        status="draft",
    )
    fake_db.queue_result(items=[fake_report])

    get_response = await client.get(f"/work-reports/{report_id}")
    assert get_response.status_code == 200


async def test_list_limit_max_100(client, auth_as, admin_user):
    auth_as(admin_user)
    response = await client.get("/work-reports/?limit=150")
    assert response.status_code == 422


async def test_generate_draft_endpoint(client, auth_as, sales_user, fake_db):
    auth_as(sales_user)
    from app.models.user import User
    fake_user = User(id=sales_user["id"], name=sales_user["name"], email=sales_user["email"], role=sales_user["role"])
    fake_db.queue_result(items=[fake_user])

    response = await client.post(
        "/work-reports/generate-draft",
        json={
            "report_type": "daily",
            "report_date": "2026-05-13",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["report_type"] == "daily"
    assert data["status"] == "draft"


async def test_update_draft_report(client, auth_as, sales_user, fake_db):
    auth_as(sales_user)
    from app.models.user import User
    from app.models.work_report import WorkReport
    fake_user = User(id=sales_user["id"], name=sales_user["name"], email=sales_user["email"], role=sales_user["role"])
    fake_db.queue_result(items=[fake_user])

    create_response = await client.post(
        "/work-reports/",
        json={
            "report_type": "daily",
            "report_date": "2026-05-13",
        },
    )
    assert create_response.status_code == 200
    report_id = create_response.json()["id"]

    fake_report = WorkReport(
        id=report_id,
        report_type="daily",
        report_date=date(2026, 5, 13),
        owner_id=sales_user["id"],
        status="draft",
    )
    fake_db.queue_result(items=[fake_report])

    update_response = await client.put(
        f"/work-reports/{report_id}",
        json={
            "remark": "今日跟进客户3家，商机推进顺利",
            "structured_snapshot": {"tampered": True},
        },
    )
    assert update_response.status_code == 200
    data = update_response.json()
    assert data["remark"] == "今日跟进客户3家，商机推进顺利"
    assert data["structured_snapshot"] is None


async def test_cannot_update_submitted_report(client, auth_as, sales_user, fake_db):
    auth_as(sales_user)
    from app.models.user import User
    from app.models.work_report import WorkReport
    fake_user = User(id=sales_user["id"], name=sales_user["name"], email=sales_user["email"], role=sales_user["role"])
    fake_db.queue_result(items=[fake_user])

    create_response = await client.post(
        "/work-reports/",
        json={
            "report_type": "daily",
            "report_date": "2026-05-13",
        },
    )
    assert create_response.status_code == 200
    report_id = create_response.json()["id"]

    fake_report = WorkReport(
        id=report_id,
        report_type="daily",
        report_date=date(2026, 5, 13),
        owner_id=sales_user["id"],
        status="submitted",
    )
    fake_db.queue_result(items=[fake_report])

    update_response = await client.put(
        f"/work-reports/{report_id}",
        json={"remark": "尝试修改已提交报告"},
    )
    assert update_response.status_code == 403


async def test_regenerate_snapshot(client, auth_as, sales_user, fake_db):
    auth_as(sales_user)
    from app.models.user import User
    from app.models.work_report import WorkReport
    fake_user = User(id=sales_user["id"], name=sales_user["name"], email=sales_user["email"], role=sales_user["role"])
    fake_db.queue_result(items=[fake_user])

    create_response = await client.post(
        "/work-reports/",
        json={
            "report_type": "daily",
            "report_date": "2026-05-13",
        },
    )
    assert create_response.status_code == 200
    report_id = create_response.json()["id"]

    fake_report = WorkReport(
        id=report_id,
        report_type="daily",
        report_date=date(2026, 5, 13),
        owner_id=sales_user["id"],
        status="draft",
    )
    fake_db.queue_result(items=[fake_report])

    regenerate_response = await client.post(f"/work-reports/{report_id}/regenerate")
    assert regenerate_response.status_code == 200


async def test_weekly_report(client, auth_as, sales_user, fake_db):
    auth_as(sales_user)
    from app.models.user import User
    fake_user = User(id=sales_user["id"], name=sales_user["name"], email=sales_user["email"], role=sales_user["role"])
    fake_db.queue_result(items=[fake_user])

    weekly_response = await client.post(
        "/work-reports/",
        json={"report_type": "weekly", "report_date": "2026-05-12"},
    )
    assert weekly_response.status_code == 200
    data = weekly_response.json()
    assert data["report_type"] == "weekly"


async def test_channel_ops_can_create_report(client, auth_as, channel_ops_user, fake_db):
    auth_as(channel_ops_user)
    from app.models.user import User
    fake_user = User(id=channel_ops_user["id"], name=channel_ops_user["name"], email=channel_ops_user["email"], role=channel_ops_user["role"])
    fake_db.queue_result(items=[fake_user])

    response = await client.post(
        "/work-reports/",
        json={"report_type": "daily", "report_date": "2026-05-13"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["report_type"] == "daily"


async def test_daily_snapshot_uses_follow_up_content(fake_db, sales_user):
    from app.models.followup import FollowUp
    from app.services.work_report_service import WorkReportService

    fake_db.queue_result(
        items=[
            FollowUp(
                id=1,
                follower_id=sales_user["id"],
                follow_up_date=date(2026, 5, 13),
                follow_up_type="business",
                follow_up_method="电话",
                follow_up_content="拜访客户并确认下一步计划",
            )
        ]
    )

    snapshot = await WorkReportService(fake_db).generate_daily_snapshot(
        sales_user["id"],
        date(2026, 5, 13),
    )

    assert snapshot["follow_ups"]["count"] == 1
    assert snapshot["follow_ups"]["items"][0]["content"] == "拜访客户并确认下一步计划"


async def test_admin_team_endpoint_returns_all_reports(client, auth_as, admin_user, sales_user, fake_db):
    auth_as(admin_user)
    from app.models.work_report import WorkReport

    report = WorkReport(
        id=42,
        report_type="daily",
        report_date=date(2026, 5, 13),
        owner_id=sales_user["id"],
        status="draft",
    )
    fake_db.queue_result(items=[report])

    response = await client.get("/work-reports/team")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == 42


async def test_team_endpoint_rejects_invalid_status(client, auth_as, admin_user):
    auth_as(admin_user)
    response = await client.get("/work-reports/team?status=invalid")
    assert response.status_code == 422


async def test_daily_snapshot_service_returns_structure(fake_db, sales_user):
    from app.services.work_report_service import WorkReportService

    fake_db.queue_result(items=[])
    fake_db.queue_result(items=[])
    fake_db.queue_result(items=[])
    fake_db.queue_result(items=[])
    fake_db.queue_result(items=[])
    fake_db.queue_result(items=[])
    fake_db.queue_result(items=[])

    snapshot = await WorkReportService(fake_db).generate_daily_snapshot(
        sales_user["id"],
        date(2026, 5, 13),
    )

    assert "follow_ups" in snapshot
    assert "leads" in snapshot
    assert "opportunities" in snapshot
    assert "projects" in snapshot
    assert "contracts" in snapshot
    assert "work_orders" in snapshot
    assert "channels" in snapshot
    assert snapshot["follow_ups"]["count"] == 0
    assert snapshot["leads"]["count"] == 0
