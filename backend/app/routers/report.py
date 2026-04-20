from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database import get_db
from app.models.contract import Contract, PaymentPlan
from app.models.lead import Lead
from app.models.opportunity import Opportunity
from app.models.project import Project
from app.schemas.report import (
    PaymentProgressResponse,
    PerformanceReportResponse,
    SalesFunnelResponse,
)


router = APIRouter(prefix="/reports", tags=["reports"])


def _resolve_sales_scope(
    current_user: dict,
    sales_owner_id: Optional[int],
) -> Optional[int]:
    role = current_user.get("role")
    user_id = current_user["id"]

    if role in {"admin", "business", "finance"}:
        return sales_owner_id

    if role == "sales":
        if sales_owner_id is not None and sales_owner_id != user_id:
            raise HTTPException(status_code=403, detail="只能查看自己的报表数据")
        return user_id

    raise HTTPException(status_code=403, detail="无权限访问报表数据")


@router.get("/sales-funnel", response_model=SalesFunnelResponse)
async def get_sales_funnel(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    sales_owner_id: Optional[int] = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    sales_owner_id = _resolve_sales_scope(current_user, sales_owner_id)

    lead_query = select(Lead)
    if start_date:
        lead_query = lead_query.where(Lead.created_at >= start_date)
    if end_date:
        lead_query = lead_query.where(Lead.created_at <= end_date)
    if sales_owner_id:
        lead_query = lead_query.where(Lead.sales_owner_id == sales_owner_id)
    lead_result = await db.execute(lead_query)
    leads = lead_result.scalars().all()

    lead_stages = {}
    for lead in leads:
        stage = lead.lead_stage
        lead_stages[stage] = lead_stages.get(stage, 0) + 1

    converted_leads = sum(1 for l in leads if l.converted_to_opportunity)
    lost_leads = sum(1 for l in leads if l.lead_stage == "已流失")

    opp_query = select(Opportunity)
    if start_date:
        opp_query = opp_query.where(Opportunity.created_at >= start_date)
    if end_date:
        opp_query = opp_query.where(Opportunity.created_at <= end_date)
    if sales_owner_id:
        opp_query = opp_query.where(Opportunity.sales_owner_id == sales_owner_id)
    opp_result = await db.execute(opp_query)
    opportunities = opp_result.scalars().all()

    opp_stages = {}
    for opp in opportunities:
        stage = opp.opportunity_stage
        opp_stages[stage] = opp_stages.get(stage, 0) + 1

    opp_total_amount = sum(float(o.expected_contract_amount or 0) for o in opportunities)
    won_opps = sum(1 for o in opportunities if o.opportunity_stage == "已成交")
    lost_opps = sum(1 for o in opportunities if o.opportunity_stage == "已流失")

    proj_query = select(Project)
    if start_date:
        proj_query = proj_query.where(Project.created_at >= start_date)
    if end_date:
        proj_query = proj_query.where(Project.created_at <= end_date)
    if sales_owner_id:
        proj_query = proj_query.where(Project.sales_owner_id == sales_owner_id)
    proj_result = await db.execute(proj_query)
    projects = proj_result.scalars().all()

    proj_statuses = {}
    for proj in projects:
        status = proj.project_status
        proj_statuses[status] = proj_statuses.get(status, 0) + 1

    proj_total_amount = sum(float(p.downstream_contract_amount or 0) for p in projects)

    contract_query = select(Contract).where(Contract.contract_direction == "Downstream")
    if start_date:
        contract_query = contract_query.where(Contract.signing_date >= start_date)
    if end_date:
        contract_query = contract_query.where(Contract.signing_date <= end_date)
    if sales_owner_id:
        contract_query = contract_query.join(Project, Contract.project_id == Project.id).where(
            Project.sales_owner_id == sales_owner_id
        )
    contract_result = await db.execute(contract_query)
    contracts = contract_result.scalars().all()

    contract_statuses = {}
    for contract in contracts:
        status = contract.contract_status
        contract_statuses[status] = contract_statuses.get(status, 0) + 1

    contract_total_amount = sum(float(c.contract_amount or 0) for c in contracts)
    lead_to_opp_rate = round(converted_leads / len(leads) * 100, 2) if leads else 0
    opp_to_proj_rate = round(won_opps / len(opportunities) * 100, 2) if opportunities else 0

    return SalesFunnelResponse(
        leads={
            "total": len(leads),
            "by_stage": lead_stages,
            "converted": converted_leads,
            "lost": lost_leads,
        },
        opportunities={
            "total": len(opportunities),
            "by_stage": opp_stages,
            "total_amount": opp_total_amount,
            "won": won_opps,
            "lost": lost_opps,
        },
        projects={
            "total": len(projects),
            "by_status": proj_statuses,
            "total_amount": proj_total_amount,
        },
        contracts={
            "total": len(contracts),
            "by_status": contract_statuses,
            "total_amount": contract_total_amount,
        },
        conversion_rates={
            "lead_to_opportunity": lead_to_opp_rate,
            "opportunity_to_project": opp_to_proj_rate,
        },
    )


@router.get("/performance", response_model=PerformanceReportResponse)
async def get_performance_report(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    sales_owner_id: Optional[int] = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _resolve_sales_scope(current_user, sales_owner_id)
    return PerformanceReportResponse(
        by_user=[],
        by_month=[],
        total_contract_amount=0.0,
        total_received_amount=0.0,
        total_pending_amount=0.0,
    )


@router.get("/payment-progress", response_model=PaymentProgressResponse)
async def get_payment_progress(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    sales_owner_id: Optional[int] = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    sales_owner_id = _resolve_sales_scope(current_user, sales_owner_id)

    contract_query = select(Contract).where(Contract.contract_direction == "Downstream")
    if sales_owner_id:
        contract_query = contract_query.join(Project, Contract.project_id == Project.id).where(
            Project.sales_owner_id == sales_owner_id
        )
    contract_result = await db.execute(contract_query)
    contracts = contract_result.scalars().all()

    contract_data = []
    total_plan = 0
    total_actual = 0
    overdue_amount = 0
    overdue_count = 0
    today = date.today()

    for contract in contracts:
        payment_query = select(PaymentPlan).where(PaymentPlan.contract_id == contract.id)
        payment_result = await db.execute(payment_query)
        payments = payment_result.scalars().all()

        plan_sum = sum(float(p.plan_amount or 0) for p in payments)
        actual_sum = sum(float(p.actual_amount or 0) for p in payments)

        contract_overdue = 0
        for payment in payments:
            if payment.plan_date and payment.plan_date < today and payment.payment_status != "completed":
                contract_overdue += float(payment.plan_amount or 0) - float(
                    payment.actual_amount or 0
                )
                overdue_count += 1

        progress = round(actual_sum / plan_sum * 100, 2) if plan_sum > 0 else 0
        contract_data.append(
            {
                "contract_id": contract.id,
                "contract_code": contract.contract_code,
                "contract_name": contract.contract_name,
                "contract_amount": float(contract.contract_amount or 0),
                "plan_amount": plan_sum,
                "actual_amount": actual_sum,
                "pending_amount": plan_sum - actual_sum,
                "overdue_amount": contract_overdue,
                "progress_percentage": progress,
                "payment_count": len(payments),
                "completed_count": sum(
                    1 for payment in payments if payment.payment_status == "completed"
                ),
            }
        )

        total_plan += plan_sum
        total_actual += actual_sum
        overdue_amount += contract_overdue

    total_pending = total_plan - total_actual
    overall_progress = round(total_actual / total_plan * 100, 2) if total_plan > 0 else 0

    return PaymentProgressResponse(
        total_plan_amount=total_plan,
        total_actual_amount=total_actual,
        total_pending_amount=total_pending,
        overdue_amount=overdue_amount,
        overdue_count=overdue_count,
        contracts=contract_data,
        progress_percentage=overall_progress,
    )
