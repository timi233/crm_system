import pytest
from fastapi import HTTPException

from app.core.policy.service import policy_service, build_principal
from app.core.policy.resources.customer import CustomerPolicy
from app.core.policy.resources.opportunity import OpportunityPolicy
from app.core.policy.resources.project import ProjectPolicy
from app.core.policy.resources.work_order import WorkOrderPolicy
from app.core.policy.resources.dashboard import DashboardPolicy


pytestmark = pytest.mark.asyncio


class MockObj:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


async def test_dashboard_policy_authorize_read_allows_known_roles(fake_db):
    policy = DashboardPolicy()
    for role in ("admin", "business", "sales", "finance", "technician"):
        principal = build_principal({"id": 1, "role": role})
        try:
            await policy.authorize(
                principal=principal,
                db=fake_db,
                action="read",
                obj=MockObj(),
            )
        except HTTPException:
            pytest.fail(f"Dashboard read should allow role={role}")


async def test_dashboard_policy_authorize_read_rejects_unknown_role(fake_db):
    policy = DashboardPolicy()
    principal = build_principal({"id": 1, "role": "unknown"})
    with pytest.raises(HTTPException) as exc_info:
        await policy.authorize(
            principal=principal,
            db=fake_db,
            action="read",
            obj=MockObj(),
        )
    assert exc_info.value.status_code == 403


async def test_dashboard_policy_authorize_manage_rejects_non_admin(fake_db):
    policy = DashboardPolicy()
    for role in ("business", "sales", "finance", "technician"):
        principal = build_principal({"id": 1, "role": role})
        with pytest.raises(HTTPException) as exc_info:
            await policy.authorize(
                principal=principal,
                db=fake_db,
                action="manage",
                obj=MockObj(),
            )
        assert exc_info.value.status_code == 403


async def test_dashboard_policy_authorize_manage_allows_admin(fake_db):
    policy = DashboardPolicy()
    principal = build_principal({"id": 1, "role": "admin"})
    await policy.authorize(
        principal=principal,
        db=fake_db,
        action="manage",
        obj=MockObj(),
    )


async def test_customer_policy_authorize_update_sales_owner(fake_db):
    policy = CustomerPolicy()
    principal = build_principal({"id": 1, "role": "sales"})
    customer = MockObj(id=100, customer_owner_id=1)
    await policy.authorize(
        principal=principal,
        db=fake_db,
        action="update",
        obj=customer,
    )


async def test_customer_policy_authorize_update_rejects_other_sales(fake_db):
    policy = CustomerPolicy()
    principal = build_principal({"id": 1, "role": "sales"})
    customer = MockObj(id=100, customer_owner_id=2)
    with pytest.raises(HTTPException) as exc_info:
        await policy.authorize(
            principal=principal,
            db=fake_db,
            action="update",
            obj=customer,
        )
    assert exc_info.value.status_code == 403


async def test_customer_policy_authorize_delete_admin(fake_db):
    policy = CustomerPolicy()
    principal = build_principal({"id": 1, "role": "admin"})
    customer = MockObj(id=100, customer_owner_id=999)
    await policy.authorize(
        principal=principal,
        db=fake_db,
        action="delete",
        obj=customer,
    )


async def test_opportunity_policy_authorize_read_sales_owner(fake_db):
    policy = OpportunityPolicy()
    principal = build_principal({"id": 1, "role": "sales"})
    opportunity = MockObj(id=100, sales_owner_id=1)
    await policy.authorize(
        principal=principal,
        db=fake_db,
        action="read",
        obj=opportunity,
    )


async def test_opportunity_policy_authorize_read_rejects_other_sales(fake_db):
    policy = OpportunityPolicy()
    principal = build_principal({"id": 1, "role": "sales"})
    opportunity = MockObj(id=100, sales_owner_id=2)
    with pytest.raises(HTTPException) as exc_info:
        await policy.authorize(
            principal=principal,
            db=fake_db,
            action="read",
            obj=opportunity,
        )
    assert exc_info.value.status_code == 403


async def test_opportunity_policy_authorize_finance_rejected(fake_db):
    policy = OpportunityPolicy()
    principal = build_principal({"id": 1, "role": "finance"})
    opportunity = MockObj(id=100, sales_owner_id=1)
    with pytest.raises(HTTPException) as exc_info:
        await policy.authorize(
            principal=principal,
            db=fake_db,
            action="read",
            obj=opportunity,
        )
    assert exc_info.value.status_code == 403


async def test_project_policy_authorize_read_sales_owner(fake_db):
    policy = ProjectPolicy()
    principal = build_principal({"id": 1, "role": "sales"})
    project = MockObj(id=100, sales_owner_id=1)
    await policy.authorize(
        principal=principal,
        db=fake_db,
        action="read",
        obj=project,
    )


async def test_project_policy_authorize_read_rejects_other_sales(fake_db):
    policy = ProjectPolicy()
    principal = build_principal({"id": 1, "role": "sales"})
    project = MockObj(id=100, sales_owner_id=2)
    with pytest.raises(HTTPException) as exc_info:
        await policy.authorize(
            principal=principal,
            db=fake_db,
            action="read",
            obj=project,
        )
    assert exc_info.value.status_code == 403


async def test_project_policy_authorize_finance_rejected(fake_db):
    policy = ProjectPolicy()
    principal = build_principal({"id": 1, "role": "finance"})
    project = MockObj(id=100, sales_owner_id=1)
    with pytest.raises(HTTPException) as exc_info:
        await policy.authorize(
            principal=principal,
            db=fake_db,
            action="read",
            obj=project,
        )
    assert exc_info.value.status_code == 403


async def test_project_policy_authorize_business(fake_db):
    policy = ProjectPolicy()
    principal = build_principal({"id": 1, "role": "business"})
    project = MockObj(id=100, sales_owner_id=999)
    await policy.authorize(
        principal=principal,
        db=fake_db,
        action="read",
        obj=project,
    )


async def test_work_order_policy_authorize_read_admin(fake_db):
    policy = WorkOrderPolicy()
    principal = build_principal({"id": 1, "role": "admin"})
    work_order = MockObj(id=100, submitter_id=999)
    await policy.authorize(
        principal=principal,
        db=fake_db,
        action="read",
        obj=work_order,
    )


async def test_work_order_policy_authorize_read_sales_owner(fake_db):
    policy = WorkOrderPolicy()
    principal = build_principal({"id": 1, "role": "sales"})
    work_order = MockObj(id=100, submitter_id=1)
    await policy.authorize(
        principal=principal,
        db=fake_db,
        action="read",
        obj=work_order,
    )


async def test_work_order_policy_authorize_read_sales_related(fake_db):
    policy = WorkOrderPolicy()
    principal = build_principal({"id": 1, "role": "sales"})
    work_order = MockObj(id=100, submitter_id=999, related_sales_id=1)
    await policy.authorize(
        principal=principal,
        db=fake_db,
        action="read",
        obj=work_order,
    )


async def test_work_order_policy_authorize_read_rejects_unrelated_sales(fake_db):
    policy = WorkOrderPolicy()
    principal = build_principal({"id": 1, "role": "sales"})
    work_order = MockObj(id=100, submitter_id=999, related_sales_id=888)
    with pytest.raises(HTTPException) as exc_info:
        await policy.authorize(
            principal=principal,
            db=fake_db,
            action="read",
            obj=work_order,
        )
    assert exc_info.value.status_code == 403