import pytest
from datetime import date

from app.models.sales_target import SalesTarget
from app.models.actual_performance import ActualPerformance
from app.models.user import User
import app.core.permissions as permissions


pytestmark = pytest.mark.asyncio


async def _noop(*args, **kwargs):
    return None


async def test_create_year_target_success(client, auth_as, admin_user, fake_db, monkeypatch):
    auth_as(admin_user)
    monkeypatch.setattr(permissions, "assert_can_mutate_entity_v2", _noop)

    fake_db.queue_result(items=[])
    fake_db.queue_result(items=[])

    response = await client.post(
        "/sales-targets/year",
        json={
            "user_id": 2,
            "target_year": 2026,
            "target_amount": 400000,
            "gross_profit_target": 80000,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == 2
    assert data["target_year"] == 2026
    assert data["target_amount"] == 400000


async def test_create_year_target_duplicate_rejected(client, auth_as, admin_user, fake_db, monkeypatch):
    auth_as(admin_user)
    monkeypatch.setattr(permissions, "assert_can_mutate_entity_v2", _noop)

    existing = SalesTarget(
        id=1,
        user_id=2,
        target_type="yearly",
        target_year=2026,
        target_period=1,
        target_amount=400000,
    )
    fake_db.queue_result(items=[existing])

    response = await client.post(
        "/sales-targets/year",
        json={
            "user_id": 2,
            "target_year": 2026,
            "target_amount": 500000,
        },
    )
    assert response.status_code == 400
    assert "已存在" in response.json()["detail"]


async def test_create_year_target_invalid_year(client, auth_as, admin_user, monkeypatch):
    auth_as(admin_user)
    monkeypatch.setattr(permissions, "assert_can_mutate_entity_v2", _noop)

    response = await client.post(
        "/sales-targets/year",
        json={
            "user_id": 2,
            "target_year": 1999,
            "target_amount": 400000,
        },
    )
    assert response.status_code == 422


async def test_create_year_target_negative_amount(client, auth_as, admin_user, monkeypatch):
    auth_as(admin_user)
    monkeypatch.setattr(permissions, "assert_can_mutate_entity_v2", _noop)

    response = await client.post(
        "/sales-targets/year",
        json={
            "user_id": 2,
            "target_year": 2026,
            "target_amount": -100,
        },
    )
    assert response.status_code == 422


async def test_decompose_idempotent(client, auth_as, admin_user, fake_db, monkeypatch):
    """拆分幂等：已存在的季度/月度更新金额，不存在则创建"""
    auth_as(admin_user)
    monkeypatch.setattr(permissions, "assert_can_mutate_entity_v2", _noop)

    year_target = SalesTarget(
        id=1,
        user_id=2,
        target_type="yearly",
        target_year=2026,
        target_period=1,
        target_amount=400000,
        gross_profit_target=80000,
    )
    existing_q1 = SalesTarget(
        id=2,
        user_id=2,
        target_type="quarterly",
        target_year=2026,
        target_period=1,
        target_amount=80000,
        parent_id=1,
    )
    fake_db.queue_result(items=[year_target])
    fake_db.queue_result(items=[existing_q1])
    fake_db.queue_result(items=[])
    fake_db.queue_result(items=[])
    fake_db.queue_result(items=[])
    fake_db.queue_result(items=[])

    response = await client.post(
        "/sales-targets/1/decompose/",
        json={
            "quarters": {1: 100000, 2: 100000, 3: 100000, 4: 100000},
            "quarters_gp": {1: 20000, 2: 20000, 3: 20000, 4: 20000},
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["updated_quarters"] == 1
    assert data["created_quarters"] == 3


async def test_decompose_invalid_quarter(client, auth_as, admin_user, fake_db, monkeypatch):
    auth_as(admin_user)
    monkeypatch.setattr(permissions, "assert_can_mutate_entity_v2", _noop)

    year_target = SalesTarget(
        id=1,
        user_id=2,
        target_type="yearly",
        target_year=2026,
        target_period=1,
        target_amount=400000,
    )
    fake_db.queue_result(items=[year_target])

    response = await client.post(
        "/sales-targets/1/decompose/",
        json={
            "quarters": {5: 100000},
        },
    )
    assert response.status_code == 400
    assert "季度编号" in response.json()["detail"]


async def test_decompose_invalid_month_for_quarter(client, auth_as, admin_user, fake_db, monkeypatch):
    auth_as(admin_user)
    monkeypatch.setattr(permissions, "assert_can_mutate_entity_v2", _noop)

    year_target = SalesTarget(
        id=1,
        user_id=2,
        target_type="yearly",
        target_year=2026,
        target_period=1,
        target_amount=400000,
    )
    fake_db.queue_result(items=[year_target])
    fake_db.queue_result(items=[])
    fake_db.queue_result(items=[])

    response = await client.post(
        "/sales-targets/1/decompose/",
        json={
            "quarters": {1: 100000},
            "months_by_quarter": {1: {5: 50000}},
        },
    )
    assert response.status_code == 400
    assert "月份" in response.json()["detail"]


async def test_decompose_sum_exceeds_year(client, auth_as, admin_user, fake_db, monkeypatch):
    auth_as(admin_user)
    monkeypatch.setattr(permissions, "assert_can_mutate_entity_v2", _noop)

    year_target = SalesTarget(
        id=1,
        user_id=2,
        target_type="yearly",
        target_year=2026,
        target_period=1,
        target_amount=400000,
    )
    fake_db.queue_result(items=[year_target])
    fake_db.queue_result(items=[])

    response = await client.post(
        "/sales-targets/1/decompose/",
        json={
            "quarters": {1: 200000, 2: 200000, 3: 100000},
        },
    )
    assert response.status_code == 400
    assert "超出年目标" in response.json()["detail"]


async def test_decompose_partial_quarter_rejects_when_existing_siblings_exceed_year(
    client, auth_as, admin_user, fake_db, monkeypatch
):
    auth_as(admin_user)
    monkeypatch.setattr(permissions, "assert_can_mutate_entity_v2", _noop)

    year_target = SalesTarget(
        id=1,
        user_id=2,
        target_type="yearly",
        target_year=2026,
        target_period=1,
        target_amount=400000,
        gross_profit_target=80000,
    )
    existing_q2 = SalesTarget(
        id=2,
        user_id=2,
        target_type="quarterly",
        target_year=2026,
        target_period=2,
        target_amount=100000,
        gross_profit_target=20000,
        parent_id=1,
    )
    fake_db.queue_result(items=[year_target])
    fake_db.queue_result(items=[existing_q2])

    response = await client.post(
        "/sales-targets/1/decompose/",
        json={
            "quarters": {1: 350000},
            "quarters_gp": {1: 70000},
        },
    )

    assert response.status_code == 400
    assert "超出年目标" in response.json()["detail"]


async def test_decompose_quarter_downsize_rejects_when_existing_months_exceed_quarter(
    client, auth_as, admin_user, fake_db, monkeypatch
):
    auth_as(admin_user)
    monkeypatch.setattr(permissions, "assert_can_mutate_entity_v2", _noop)

    year_target = SalesTarget(
        id=1,
        user_id=2,
        target_type="yearly",
        target_year=2026,
        target_period=1,
        target_amount=400000,
        gross_profit_target=80000,
    )
    q1 = SalesTarget(
        id=2,
        user_id=2,
        target_type="quarterly",
        target_year=2026,
        target_period=1,
        target_amount=100000,
        gross_profit_target=20000,
        parent_id=1,
    )
    m1 = SalesTarget(
        id=3,
        user_id=2,
        target_type="monthly",
        target_year=2026,
        target_period=1,
        target_amount=60000,
        gross_profit_target=12000,
        parent_id=2,
    )
    fake_db.queue_result(items=[year_target])
    fake_db.queue_result(items=[q1])
    fake_db.queue_result(items=[m1])

    response = await client.post(
        "/sales-targets/1/decompose/",
        json={
            "quarters": {1: 50000},
            "quarters_gp": {1: 10000},
        },
    )

    assert response.status_code == 400
    assert "月度营收合计" in response.json()["detail"]


async def test_decompose_partial_month_rejects_when_existing_months_exceed_quarter(
    client, auth_as, admin_user, fake_db, monkeypatch
):
    auth_as(admin_user)
    monkeypatch.setattr(permissions, "assert_can_mutate_entity_v2", _noop)

    year_target = SalesTarget(
        id=1,
        user_id=2,
        target_type="yearly",
        target_year=2026,
        target_period=1,
        target_amount=400000,
        gross_profit_target=80000,
    )
    q1 = SalesTarget(
        id=2,
        user_id=2,
        target_type="quarterly",
        target_year=2026,
        target_period=1,
        target_amount=100000,
        gross_profit_target=20000,
        parent_id=1,
    )
    m2 = SalesTarget(
        id=3,
        user_id=2,
        target_type="monthly",
        target_year=2026,
        target_period=2,
        target_amount=70000,
        gross_profit_target=14000,
        parent_id=2,
    )
    fake_db.queue_result(items=[year_target])
    fake_db.queue_result(items=[q1])
    fake_db.queue_result(items=[m2])

    response = await client.post(
        "/sales-targets/1/decompose/",
        json={
            "quarters": {1: 100000},
            "quarters_gp": {1: 20000},
            "months_by_quarter": {1: {1: 40000}},
            "months_gp_by_quarter": {1: {1: 8000}},
        },
    )

    assert response.status_code == 400
    assert "月度营收合计" in response.json()["detail"]


async def test_update_quarterly_target_success(client, auth_as, admin_user, fake_db, monkeypatch):
    auth_as(admin_user)
    monkeypatch.setattr(permissions, "assert_can_mutate_entity_v2", _noop)

    quarter_target = SalesTarget(
        id=2,
        user_id=2,
        target_type="quarterly",
        target_year=2026,
        target_period=1,
        target_amount=100000,
        parent_id=1,
    )
    year_target = SalesTarget(
        id=1,
        user_id=2,
        target_type="yearly",
        target_year=2026,
        target_period=1,
        target_amount=400000,
    )
    fake_db.queue_result(items=[quarter_target])
    fake_db.queue_result(items=[])
    fake_db.queue_result(items=[year_target])
    fake_db.queue_result(items=[])

    response = await client.put(
        "/sales-targets/2",
        json={"target_amount": 120000},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["target_amount"] == 120000


async def test_update_quarterly_exceeds_parent(client, auth_as, admin_user, fake_db, monkeypatch):
    auth_as(admin_user)
    monkeypatch.setattr(permissions, "assert_can_mutate_entity_v2", _noop)

    quarter_target = SalesTarget(
        id=2,
        user_id=2,
        target_type="quarterly",
        target_year=2026,
        target_period=1,
        target_amount=100000,
        parent_id=1,
    )
    year_target = SalesTarget(
        id=1,
        user_id=2,
        target_type="yearly",
        target_year=2026,
        target_period=1,
        target_amount=400000,
    )
    other_quarter = SalesTarget(
        id=3,
        user_id=2,
        target_type="quarterly",
        target_year=2026,
        target_period=2,
        target_amount=150000,
        parent_id=1,
    )
    fake_db.queue_result(items=[quarter_target])
    fake_db.queue_result(items=[])
    fake_db.queue_result(items=[year_target])
    fake_db.queue_result(items=[other_quarter])

    response = await client.put(
        "/sales-targets/2",
        json={"target_amount": 300000},
    )
    assert response.status_code == 400
    assert "超父目标" in response.json()["detail"]


async def test_update_monthly_target_success(client, auth_as, admin_user, fake_db, monkeypatch):
    auth_as(admin_user)
    monkeypatch.setattr(permissions, "assert_can_mutate_entity_v2", _noop)

    month_target = SalesTarget(
        id=3,
        user_id=2,
        target_type="monthly",
        target_year=2026,
        target_period=1,
        target_amount=30000,
        parent_id=2,
    )
    quarter_target = SalesTarget(
        id=2,
        user_id=2,
        target_type="quarterly",
        target_year=2026,
        target_period=1,
        target_amount=100000,
        parent_id=1,
    )
    fake_db.queue_result(items=[month_target])
    fake_db.queue_result(items=[])
    fake_db.queue_result(items=[quarter_target])
    fake_db.queue_result(items=[])

    response = await client.put(
        "/sales-targets/3",
        json={"target_amount": 35000},
    )
    assert response.status_code == 200


async def test_delete_quarterly_with_children_rejected(client, auth_as, admin_user, fake_db, monkeypatch):
    auth_as(admin_user)
    monkeypatch.setattr(permissions, "assert_can_mutate_entity_v2", _noop)

    quarter_target = SalesTarget(
        id=2,
        user_id=2,
        target_type="quarterly",
        target_year=2026,
        target_period=1,
        target_amount=100000,
        parent_id=1,
    )
    month_target = SalesTarget(
        id=3,
        user_id=2,
        target_type="monthly",
        target_year=2026,
        target_period=1,
        target_amount=30000,
        parent_id=2,
    )
    fake_db.queue_result(items=[quarter_target])
    fake_db.queue_result(items=[month_target])

    response = await client.delete("/sales-targets/2")
    assert response.status_code == 400
    assert "请先删除下级目标" in response.json()["detail"]


async def test_delete_monthly_with_actual_rejected(client, auth_as, admin_user, fake_db, monkeypatch):
    auth_as(admin_user)
    monkeypatch.setattr(permissions, "assert_can_mutate_entity_v2", _noop)

    month_target = SalesTarget(
        id=3,
        user_id=2,
        target_type="monthly",
        target_year=2026,
        target_period=1,
        target_amount=30000,
        parent_id=2,
    )
    actual = ActualPerformance(
        id=1,
        user_id=2,
        target_id=3,
        year=2026,
        month=1,
        amount_actual=25000,
    )
    fake_db.queue_result(items=[month_target])
    fake_db.queue_result(items=[])
    fake_db.queue_result(items=[actual])

    response = await client.delete("/sales-targets/3")
    assert response.status_code == 400
    assert "实际业绩" in response.json()["detail"]


async def test_delete_monthly_without_actual_success(client, auth_as, admin_user, fake_db, monkeypatch):
    auth_as(admin_user)
    monkeypatch.setattr(permissions, "assert_can_mutate_entity_v2", _noop)

    month_target = SalesTarget(
        id=3,
        user_id=2,
        target_type="monthly",
        target_year=2026,
        target_period=1,
        target_amount=30000,
        parent_id=2,
    )
    fake_db.queue_result(items=[month_target])
    fake_db.queue_result(items=[])
    fake_db.queue_result(items=[])

    response = await client.delete("/sales-targets/3")
    assert response.status_code == 200
    assert response.json()["success"] is True


async def test_create_actual_with_user_id(client, auth_as, admin_user, fake_db, monkeypatch):
    """管理员代填实际业绩，指定user_id"""
    auth_as(admin_user)
    monkeypatch.setattr(permissions, "assert_can_mutate_entity_v2", _noop)

    fake_db.queue_result(items=[])
    fake_db.queue_result(items=[])

    response = await client.post(
        "/sales-targets/actual/",
        json={
            "user_id": 5,
            "year": 2026,
            "month": 1,
            "amount_actual": 50000,
            "gross_profit_actual": 10000,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == 5


async def test_create_actual_non_admin_cannot_fill_for_others(client, auth_as, sales_user, fake_db, monkeypatch):
    auth_as(sales_user)
    monkeypatch.setattr(permissions, "assert_can_mutate_entity_v2", _noop)

    fake_db.queue_result(items=[])

    response = await client.post(
        "/sales-targets/actual/",
        json={
            "user_id": 5,
            "year": 2026,
            "month": 1,
            "amount_actual": 50000,
        },
    )
    assert response.status_code == 403


async def test_create_actual_duplicate_rejected(client, auth_as, admin_user, fake_db, monkeypatch):
    auth_as(admin_user)
    monkeypatch.setattr(permissions, "assert_can_mutate_entity_v2", _noop)

    existing = ActualPerformance(
        id=1,
        user_id=2,
        year=2026,
        month=1,
        amount_actual=30000,
    )
    fake_db.queue_result(items=[existing])

    response = await client.post(
        "/sales-targets/actual/",
        json={
            "user_id": 2,
            "year": 2026,
            "month": 1,
            "amount_actual": 50000,
        },
    )
    assert response.status_code == 409


async def test_create_actual_with_target_id_validates_match(client, auth_as, admin_user, fake_db, monkeypatch):
    """创建实际业绩关联月度目标时校验年月归属一致性"""
    auth_as(admin_user)
    monkeypatch.setattr(permissions, "assert_can_mutate_entity_v2", _noop)

    month_target = SalesTarget(
        id=3,
        user_id=2,
        target_type="monthly",
        target_year=2026,
        target_period=1,
        target_amount=30000,
        parent_id=2,
    )
    fake_db.queue_result(items=[])
    fake_db.queue_result(items=[month_target])

    response = await client.post(
        "/sales-targets/actual/",
        json={
            "user_id": 2,
            "target_id": 3,
            "year": 2025,
            "month": 1,
            "amount_actual": 50000,
        },
    )
    assert response.status_code == 400
    assert "年月" in response.json()["detail"]


async def test_update_actual_target_id_validates_match(client, auth_as, admin_user, fake_db, monkeypatch):
    """更新实际业绩关联目标时同样校验年月和归属一致性"""
    auth_as(admin_user)
    monkeypatch.setattr(permissions, "assert_can_mutate_entity_v2", _noop)

    record = ActualPerformance(
        id=1,
        user_id=2,
        year=2026,
        month=1,
        amount_actual=30000,
    )
    wrong_month_target = SalesTarget(
        id=4,
        user_id=2,
        target_type="monthly",
        target_year=2026,
        target_period=2,
        target_amount=30000,
        parent_id=2,
    )
    fake_db.queue_result(items=[record])
    fake_db.queue_result(items=[wrong_month_target])

    response = await client.put(
        "/sales-targets/actual/1",
        json={"target_id": 4},
    )

    assert response.status_code == 400
    assert "月份" in response.json()["detail"]


async def test_actual_summary_month_aggregation(client, auth_as, admin_user, fake_db, monkeypatch):
    auth_as(admin_user)
    monkeypatch.setattr(permissions, "assert_can_mutate_entity_v2", _noop)

    actual1 = ActualPerformance(
        id=1,
        user_id=2,
        year=2026,
        month=1,
        amount_actual=30000,
        gross_profit_actual=6000,
    )
    actual2 = ActualPerformance(
        id=2,
        user_id=2,
        year=2026,
        month=2,
        amount_actual=40000,
        gross_profit_actual=8000,
    )
    fake_db.queue_result(items=[actual1, actual2])

    response = await client.get("/sales-targets/actual/summary?group_by=month&year=2026")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert any(d["month"] == 1 and d["amount_actual"] == 30000 for d in data)
    assert any(d["month"] == 2 and d["amount_actual"] == 40000 for d in data)


async def test_actual_summary_quarter_aggregation(client, auth_as, admin_user, fake_db, monkeypatch):
    auth_as(admin_user)
    monkeypatch.setattr(permissions, "assert_can_mutate_entity_v2", _noop)

    actual1 = ActualPerformance(
        id=1,
        user_id=2,
        year=2026,
        month=1,
        amount_actual=30000,
    )
    actual2 = ActualPerformance(
        id=2,
        user_id=2,
        year=2026,
        month=2,
        amount_actual=40000,
    )
    actual3 = ActualPerformance(
        id=3,
        user_id=2,
        year=2026,
        month=4,
        amount_actual=50000,
    )
    fake_db.queue_result(items=[actual1, actual2, actual3])

    response = await client.get("/sales-targets/actual/summary?group_by=quarter&year=2026")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    q1 = next(d for d in data if d["quarter"] == 1)
    q2 = next(d for d in data if d["quarter"] == 2)
    assert q1["amount_actual"] == 70000
    assert q2["amount_actual"] == 50000


async def test_actual_summary_year_aggregation(client, auth_as, admin_user, fake_db, monkeypatch):
    auth_as(admin_user)
    monkeypatch.setattr(permissions, "assert_can_mutate_entity_v2", _noop)

    actual1 = ActualPerformance(
        id=1,
        user_id=2,
        year=2026,
        month=1,
        amount_actual=30000,
    )
    actual2 = ActualPerformance(
        id=2,
        user_id=2,
        year=2026,
        month=6,
        amount_actual=40000,
    )
    actual3 = ActualPerformance(
        id=3,
        user_id=3,
        year=2026,
        month=3,
        amount_actual=50000,
    )
    fake_db.queue_result(items=[actual1, actual2, actual3])

    response = await client.get("/sales-targets/actual/summary?group_by=year&year=2026")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    user2 = next(d for d in data if d["user_id"] == 2)
    user3 = next(d for d in data if d["user_id"] == 3)
    assert user2["amount_actual"] == 70000
    assert user3["amount_actual"] == 50000


async def test_actual_summary_invalid_group_by(client, auth_as, admin_user):
    auth_as(admin_user)

    response = await client.get("/sales-targets/actual/summary?group_by=invalid")
    assert response.status_code == 422


async def test_tree_endpoint(client, auth_as, admin_user, fake_db, monkeypatch):
    auth_as(admin_user)
    monkeypatch.setattr(permissions, "assert_can_mutate_entity_v2", _noop)

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
    m1 = SalesTarget(
        id=3,
        user_id=2,
        target_type="monthly",
        target_year=2026,
        target_period=1,
        target_amount=30000,
        parent_id=2,
    )
    fake_db.queue_result(items=[year_target])
    fake_db.queue_result(items=[year_target])
    fake_db.queue_result(items=[q1])
    fake_db.queue_result(items=[m1])
    fake_db.queue_result(items=[])
    fake_db.queue_result(items=[])
    fake_db.queue_result(items=[])
    fake_db.queue_result(items=[])

    response = await client.get("/sales-targets/tree?year=2026")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["target_year"] == 2026
    assert len(data[0]["quarters"]) == 1
