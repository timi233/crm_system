"""
Finance view service for CRM system.

Provides financial-specific data views for finance role users,
excluding sensitive business data (follow-ups, lead sources, etc.)
"""

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from decimal import Decimal
from typing import Optional

from app.models.customer import TerminalCustomer
from app.models.contract import Contract, PaymentPlan
from app.models.project import Project
from app.schemas.finance_view import (
    CustomerFinanceView,
    ContractFinanceView,
    PaymentPlanView,
    ProjectFinanceView,
)


class FinanceViewService:
    """Service for generating finance-specific customer views."""

    async def get_customer_finance_view(
        self, customer_id: int, db: AsyncSession
    ) -> CustomerFinanceView:
        """
        Get finance-specific view of a customer.

        Returns only financial data: contracts, payment plans, project financials.
        Excludes sensitive business data.
        """
        # 1. Get customer basic info
        result = await db.execute(
            select(TerminalCustomer).where(TerminalCustomer.id == customer_id)
        )
        customer = result.scalar_one_or_none()
        if not customer:
            return None

        # 2. Get contracts for this customer
        contracts_result = await db.execute(
            select(Contract).where(Contract.terminal_customer_id == customer_id)
        )
        contracts = contracts_result.scalars().all()

        # 3. Get payment plans for all contracts
        contract_ids = [c.id for c in contracts]
        payment_plans = []
        if contract_ids:
            payment_plans_result = await db.execute(
                select(PaymentPlan, Contract.contract_code, Contract.contract_name)
                .join(Contract, PaymentPlan.contract_id == Contract.id)
                .where(PaymentPlan.contract_id.in_(contract_ids))
            )
            for row in payment_plans_result.all():
                plan = row[0]
                payment_plans.append(
                    PaymentPlanView(
                        id=plan.id,
                        contract_code=row[1],
                        contract_name=row[2],
                        plan_stage=plan.plan_stage,
                        plan_amount=plan.plan_amount,
                        plan_date=plan.plan_date,
                        actual_amount=plan.actual_amount,
                        actual_date=plan.actual_date,
                        payment_status=plan.payment_status,
                    )
                )

        # 4. Get projects for this customer (financial fields only)
        projects_result = await db.execute(
            select(Project).where(Project.terminal_customer_id == customer_id)
        )
        projects = projects_result.scalars().all()

        # 5. Build finance view
        return self._build_finance_view(
            customer=customer,
            contracts=contracts,
            payment_plans=payment_plans,
            projects=projects,
        )

    def _build_finance_view(
        self,
        customer: TerminalCustomer,
        contracts: list,
        payment_plans: list,
        projects: list,
    ) -> CustomerFinanceView:
        """Build the finance view from collected data."""

        # Contract finance views
        contract_views = [
            ContractFinanceView(
                id=c.id,
                contract_code=c.contract_code,
                contract_name=c.contract_name,
                contract_direction=c.contract_direction,
                contract_status=c.contract_status,
                contract_amount=c.contract_amount,
                signing_date=c.signing_date,
                effective_date=c.effective_date,
                expiry_date=c.expiry_date,
            )
            for c in contracts
        ]

        # Project finance views
        project_views = [
            ProjectFinanceView(
                id=p.id,
                project_code=p.project_code,
                project_name=p.project_name,
                project_status=p.project_status,
                downstream_contract_amount=p.downstream_contract_amount,
                upstream_procurement_amount=p.upstream_procurement_amount,
                direct_project_investment=p.direct_project_investment,
                additional_investment=p.additional_investment,
                gross_margin=p.gross_margin,
                actual_payment_amount=p.actual_payment_amount,
                winning_date=p.winning_date,
                acceptance_date=p.acceptance_date,
                first_payment_date=p.first_payment_date,
            )
            for p in projects
        ]

        # Calculate summaries
        total_contract_amount = sum(c.contract_amount for c in contracts)
        downstream_amount = sum(
            c.contract_amount for c in contracts if c.contract_direction == "Downstream"
        )
        upstream_amount = sum(
            c.contract_amount for c in contracts if c.contract_direction == "Upstream"
        )
        signed_count = sum(1 for c in contracts if c.contract_status == "signed")
        pending_count = sum(
            1 for c in contracts if c.contract_status in ["draft", "pending"]
        )

        total_planned = sum(p.plan_amount for p in payment_plans)
        total_actual = sum(p.actual_amount or Decimal("0") for p in payment_plans)
        completion_rate = (
            float(total_actual / total_planned * 100) if total_planned > 0 else 0.0
        )

        total_project_downstream = sum(p.downstream_contract_amount for p in projects)
        total_project_upstream = (
            sum(p.upstream_procurement_amount or Decimal("0") for p in projects)
            if any(p.upstream_procurement_amount for p in projects)
            else None
        )
        total_margin = (
            sum(p.gross_margin or Decimal("0") for p in projects)
            if any(p.gross_margin for p in projects)
            else None
        )

        return CustomerFinanceView(
            customer_id=customer.id,
            customer_name=customer.customer_name,
            customer_code=customer.customer_code,
            credit_code=customer.credit_code,
            customer_status=customer.customer_status,
            contracts=contract_views,
            total_contract_amount=total_contract_amount,
            downstream_contract_amount=downstream_amount,
            upstream_contract_amount=upstream_amount,
            signed_contract_count=signed_count,
            pending_contract_count=pending_count,
            payment_plans=payment_plans,
            total_planned_amount=total_planned,
            total_actual_amount=total_actual,
            payment_completion_rate=round(completion_rate, 2),
            projects=project_views,
            total_project_downstream=total_project_downstream,
            total_project_upstream=total_project_upstream,
            total_gross_margin=total_margin,
        )


# Singleton instance
finance_view_service = FinanceViewService()
