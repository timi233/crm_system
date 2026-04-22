import pytest

from app.models.sales_target import SalesTarget


pytestmark = pytest.mark.asyncio


async def test_update_year_target_rejects_when_children_sum_mismatches(
    client, auth_as, admin_user, fake_db
):
    auth_as(admin_user)

    year_target = SalesTarget(
        id=1,
        user_id=2,
        target_type="yearly",
        target_year=2026,
        target_period=1,
        target_amount=400000,
    )
    q1 = SalesTarget(
        id=2,
        user_id=2,
        target_type="quarterly",
        target_year=2026,
        target_period=1,
        target_amount=100000,
        parent_id=1,
    )
    q2 = SalesTarget(
        id=3,
        user_id=2,
        target_type="quarterly",
        target_year=2026,
        target_period=2,
        target_amount=100000,
        parent_id=1,
    )
    q3 = SalesTarget(
        id=4,
        user_id=2,
        target_type="quarterly",
        target_year=2026,
        target_period=3,
        target_amount=100000,
        parent_id=1,
    )
    q4 = SalesTarget(
        id=5,
        user_id=2,
        target_type="quarterly",
        target_year=2026,
        target_period=4,
        target_amount=100000,
        parent_id=1,
    )
    fake_db.queue_result(items=[year_target])
    fake_db.queue_result(items=[q1, q2, q3, q4])

    response = await client.put(
        "/sales-targets/1",
        json={"user_id": 2, "target_year": 2026, "target_amount": 300000},
    )

    assert response.status_code == 400
    assert "季度目标总和" in response.json()["detail"]


async def test_delete_year_target_rejects_when_children_exist(
    client, auth_as, admin_user, fake_db
):
    auth_as(admin_user)

    year_target = SalesTarget(
        id=1,
        user_id=2,
        target_type="yearly",
        target_year=2026,
        target_period=1,
        target_amount=400000,
    )
    q1 = SalesTarget(
        id=2,
        user_id=2,
        target_type="quarterly",
        target_year=2026,
        target_period=1,
        target_amount=100000,
        parent_id=1,
    )
    fake_db.queue_result(items=[year_target])
    fake_db.queue_result(items=[q1])

    response = await client.delete("/sales-targets/1")

    assert response.status_code == 400
    assert "请先删除下级目标" in response.json()["detail"]
