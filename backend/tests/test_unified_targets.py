import pytest

from app.models.channel import Channel
from app.models.unified_target import TargetType, UnifiedTarget


pytestmark = pytest.mark.asyncio


async def test_create_unified_target_requires_auth(client):
    response = await client.post(
        "/unified-targets/",
        json={
            "target_type": "channel",
            "channel_id": 11,
            "year": 2026,
        },
    )
    assert response.status_code == 401


async def test_create_unified_target_returns_channel_name(
    client, auth_as, admin_user, fake_db
):
    auth_as(admin_user)

    fake_db.queue_result(items=[Channel(id=11, company_name="测试渠道")])
    annual = UnifiedTarget(
        id=99,
        target_type=TargetType.channel,
        channel_id=11,
        user_id=None,
        year=2026,
        quarter=None,
        month=None,
        performance_target=400000,
        opportunity_target=40,
        project_count_target=12,
    )
    fake_db.queue_result(items=[annual])

    created = UnifiedTarget(
        id=1,
        target_type=TargetType.channel,
        channel_id=11,
        user_id=None,
        year=2026,
        quarter=2,
        month=None,
        performance_target=100000,
        opportunity_target=10,
        project_count_target=3,
        development_goal="test",
        created_by=1,
    )
    created.channel = Channel(id=11, company_name="测试渠道")
    fake_db.queue_result(items=[created])

    response = await client.post(
        "/unified-targets/",
        json={
            "target_type": "channel",
            "channel_id": 11,
            "user_id": None,
            "year": 2026,
            "quarter": 2,
            "month": None,
            "performance_target": 100000,
            "opportunity_target": 10,
            "project_count_target": 3,
            "development_goal": "test",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["channel_name"] == "测试渠道"
    assert payload["target_type"] == "channel"
    assert payload["performance_target"] == "100000"


async def test_delete_unified_target_removes_target_from_storage(
    client, auth_as, admin_user, fake_db
):
    auth_as(admin_user)

    target = UnifiedTarget(
        id=9,
        target_type=TargetType.channel,
        channel_id=11,
        user_id=None,
        year=2026,
    )
    fake_db.add(target)
    fake_db.queue_result(items=[target])

    response = await client.delete("/unified-targets/9")

    assert response.status_code == 200
    assert target not in fake_db.storage.get(UnifiedTarget, [])


async def test_create_quarterly_target_requires_annual_target(
    client, auth_as, admin_user, fake_db
):
    auth_as(admin_user)
    fake_db.queue_result(items=[Channel(id=11, company_name="测试渠道")])
    fake_db.queue_result(items=[])

    response = await client.post(
        "/unified-targets/",
        json={
            "target_type": "channel",
            "channel_id": 11,
            "user_id": None,
            "year": 2026,
            "quarter": 1,
            "month": None,
            "performance_target": 100000,
            "opportunity_target": 10,
            "project_count_target": 3,
            "development_goal": "test",
        },
    )

    assert response.status_code == 400
    assert "请先创建年目标" in response.json()["detail"]


async def test_create_quarterly_target_rejects_duplicate_quarter(
    client, auth_as, admin_user, fake_db
):
    auth_as(admin_user)
    fake_db.queue_result(items=[Channel(id=11, company_name="测试渠道")])

    annual = UnifiedTarget(
        id=1,
        target_type=TargetType.channel,
        channel_id=11,
        user_id=None,
        year=2026,
        quarter=None,
        month=None,
        performance_target=400000,
        opportunity_target=40,
        project_count_target=12,
    )
    q1 = UnifiedTarget(
        id=2,
        target_type=TargetType.channel,
        channel_id=11,
        user_id=None,
        year=2026,
        quarter=1,
        month=None,
        performance_target=100000,
        opportunity_target=10,
        project_count_target=3,
    )
    fake_db.queue_result(items=[annual, q1])

    response = await client.post(
        "/unified-targets/",
        json={
            "target_type": "channel",
            "channel_id": 11,
            "user_id": None,
            "year": 2026,
            "quarter": 1,
            "month": None,
            "performance_target": 100000,
            "opportunity_target": 10,
            "project_count_target": 3,
            "development_goal": "dup",
        },
    )

    assert response.status_code == 400
    assert "不能重复创建" in response.json()["detail"]


async def test_delete_annual_target_rejects_when_quarter_targets_exist(
    client, auth_as, admin_user, fake_db
):
    auth_as(admin_user)

    annual = UnifiedTarget(
        id=9,
        target_type=TargetType.channel,
        channel_id=11,
        user_id=None,
        year=2026,
        quarter=None,
        month=None,
        performance_target=400000,
    )
    q1 = UnifiedTarget(
        id=10,
        target_type=TargetType.channel,
        channel_id=11,
        user_id=None,
        year=2026,
        quarter=1,
        month=None,
        performance_target=100000,
    )
    fake_db.queue_result(items=[annual])
    fake_db.queue_result(items=[q1])

    response = await client.delete("/unified-targets/9")

    assert response.status_code == 400
    assert "请先删除该年目标下的季度目标" in response.json()["detail"]
