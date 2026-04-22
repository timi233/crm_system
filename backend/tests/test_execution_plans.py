import pytest
from datetime import datetime, timezone

from app.models.execution_plan import ExecutionPlan, ExecutionPlanStatus, PlanCategory, PlanType
from app.models.channel import Channel
from app.models.user import User


pytestmark = pytest.mark.asyncio


async def test_list_execution_plans_requires_auth(client):
    response = await client.get("/execution-plans/")
    assert response.status_code == 401


async def test_list_execution_plans_supports_plan_category_filter(
    client, auth_as, admin_user
):
    auth_as(admin_user)
    response = await client.get("/execution-plans/?plan_category=training")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


async def test_list_execution_plans_rejects_invalid_plan_category(
    client, auth_as, admin_user
):
    auth_as(admin_user)
    response = await client.get("/execution-plans/?plan_category=invalid-category")
    assert response.status_code == 400


async def test_list_execution_plans_returns_related_user_and_channel_names(
    client, auth_as, admin_user, fake_db
):
    auth_as(admin_user)

    plan = ExecutionPlan(
        id=1,
        channel_id=10,
        user_id=20,
        plan_type=PlanType.monthly,
        plan_category=PlanCategory.training,
        plan_period="2026-04",
        plan_content="渠道培训跟进",
        execution_status="进行中",
        status=ExecutionPlanStatus.planned,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    plan.channel = Channel(id=10, company_name="华东渠道")
    plan.user = User(id=20, name="张三", email="owner@example.com", role="sales")
    fake_db.queue_result(items=[plan])

    response = await client.get("/execution-plans/?plan_category=training")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["channel_name"] == "华东渠道"
    assert payload[0]["user_name"] == "张三"
