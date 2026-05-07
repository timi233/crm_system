import pytest

from app.models.customer import TerminalCustomer
from app.models.project import Project
from app.routers.financials import export_projects


pytestmark = pytest.mark.asyncio


async def test_project_financial_export_uses_project_scope(
    fake_db, finance_user, monkeypatch
):
    calls = {}

    async def fake_authorize(**kwargs):
        calls["authorize_resource"] = kwargs["resource"]
        return None

    async def fake_scope_query(**kwargs):
        calls["scope_resource"] = kwargs["resource"]
        calls["scope_action"] = kwargs["action"]
        return kwargs["query"]

    monkeypatch.setattr(
        "app.routers.financials.policy_service.authorize",
        fake_authorize,
    )
    monkeypatch.setattr(
        "app.routers.financials.policy_service.scope_query",
        fake_scope_query,
    )

    project = Project(
        id=1,
        project_code="P-001",
        terminal_customer_id=1,
        downstream_contract_amount=1000,
        business_type="集成",
        project_status="进行中",
    )
    customer = TerminalCustomer(id=1, customer_name="Acme")
    fake_db.queue_result(rows=[(project, customer)])

    rows = await export_projects(current_user=finance_user, db=fake_db)

    assert calls == {
        "authorize_resource": "financial_export",
        "scope_resource": "project",
        "scope_action": "financial_export",
    }
    assert rows[0]["project_code"] == "P-001"
