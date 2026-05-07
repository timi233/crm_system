from decimal import Decimal

import pytest

from app.models.project import Project


pytestmark = pytest.mark.asyncio


def _project_with_financials() -> Project:
    return Project(
        id=1,
        project_code="PRJ-001",
        project_name="测试项目",
        terminal_customer_id=1,
        sales_owner_id=2,
        business_type="新建",
        project_status="进行中",
        downstream_contract_amount=Decimal("100000.00"),
        upstream_procurement_amount=Decimal("30000.00"),
        direct_project_investment=Decimal("10000.00"),
        additional_investment=Decimal("5000.00"),
        gross_margin=Decimal("55000.00"),
        product_ids=[],
        products=[],
    )


async def test_sales_project_list_hides_financial_fields(client, auth_as, sales_user, fake_db):
    auth_as(sales_user)
    fake_db.queue_result(items=[_project_with_financials()])

    response = await client.get("/projects/")

    assert response.status_code == 200
    project = response.json()[0]
    assert "upstream_procurement_amount" not in project
    assert "direct_project_investment" not in project
    assert "additional_investment" not in project
    assert "gross_margin" not in project
    assert project["downstream_contract_amount"] == 100000.0


async def test_admin_project_list_includes_financial_fields(client, auth_as, admin_user, fake_db):
    auth_as(admin_user)
    fake_db.queue_result(items=[_project_with_financials()])

    response = await client.get("/projects/")

    assert response.status_code == 200
    project = response.json()[0]
    assert project["upstream_procurement_amount"] == 30000.0
    assert project["direct_project_investment"] == 10000.0
    assert project["additional_investment"] == 5000.0
    assert project["gross_margin"] == 55000.0
