from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload
from typing import Optional

from app.database import get_db
from app.core.dependencies import get_current_user
from app.models.customer import TerminalCustomer
from app.models.channel import Channel
from app.models.lead import Lead
from app.models.opportunity import Opportunity
from app.models.project import Project
from app.models.followup import FollowUp
from app.models.contract import Contract
from app.models.work_order import WorkOrder, WorkOrderTechnician
from app.models.user import User
from app.schemas.customer_view import CustomerFullView
from app.schemas.finance_view import CustomerFinanceView

router = APIRouter(tags=["customers"])


@router.get("/customers/{customer_id}/full-view", response_model=CustomerFullView)
async def get_customer_full_view(
    customer_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_role = current_user.get("role")
    user_id = current_user["id"]

    result = await db.execute(
        select(TerminalCustomer)
        .options(
            selectinload(TerminalCustomer.owner), selectinload(TerminalCustomer.channel)
        )
        .where(TerminalCustomer.id == customer_id)
    )
    customer = result.scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    if user_role == "admin" or user_role == "business":
        pass
    elif user_role == "finance":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="财务角色请使用 /customers/{id}/finance-view 接口",
        )
    elif user_role == "sales":
        if customer.customer_owner_id != user_id:
            raise HTTPException(status_code=403, detail="无权限访问此客户")
    elif user_role == "technician":
        from sqlalchemy import and_ as sql_and

        has_access_stmt = select(WorkOrder).where(
            sql_and(
                or_(
                    WorkOrder.lead_id.in_(
                        select(Lead.id).where(Lead.terminal_customer_id == customer_id)
                    ),
                    WorkOrder.opportunity_id.in_(
                        select(Opportunity.id).where(
                            Opportunity.terminal_customer_id == customer_id
                        )
                    ),
                    WorkOrder.project_id.in_(
                        select(Project.id).where(
                            Project.terminal_customer_id == customer_id
                        )
                    ),
                ),
                WorkOrder.id.in_(
                    select(WorkOrderTechnician.work_order_id).where(
                        WorkOrderTechnician.technician_id == user_id
                    )
                ),
            )
        )
        has_access_result = await db.execute(has_access_stmt)
        if not has_access_result.scalar_one_or_none():
            raise HTTPException(status_code=403, detail="无权限访问此客户")
    else:
        raise HTTPException(status_code=403, detail="无权限访问客户数据")

    channel_data = None
    if customer.channel:
        channel_data = {
            "id": customer.channel.id,
            "channel_code": customer.channel.channel_code,
            "company_name": customer.channel.company_name,
            "channel_type": customer.channel.channel_type,
            "status": customer.channel.status,
            "main_contact": customer.channel.main_contact,
            "phone": customer.channel.phone,
        }

    leads_result = await db.execute(
        select(Lead, User.name)
        .outerjoin(User, Lead.sales_owner_id == User.id)
        .where(Lead.terminal_customer_id == customer_id)
    )
    leads_rows = leads_result.all()
    leads = []
    for row in leads_rows:
        lead = row[0]
        owner_name = row[1]
        leads.append(
            {
                "id": lead.id,
                "lead_code": lead.lead_code,
                "lead_name": lead.lead_name,
                "lead_stage": lead.lead_stage,
                "lead_source": lead.lead_source,
                "estimated_budget": float(lead.estimated_budget)
                if lead.estimated_budget
                else None,
                "sales_owner_name": owner_name,
                "converted_to_opportunity": lead.converted_to_opportunity,
            }
        )

    opps_result = await db.execute(
        select(Opportunity, User.name, Channel.company_name)
        .outerjoin(User, Opportunity.sales_owner_id == User.id)
        .outerjoin(Channel, Opportunity.channel_id == Channel.id)
        .where(Opportunity.terminal_customer_id == customer_id)
    )
    opps_rows = opps_result.all()
    opportunities = []
    for row in opps_rows:
        opp = row[0]
        owner_name = row[1]
        channel_name = row[2]
        opportunities.append(
            {
                "id": opp.id,
                "opportunity_code": opp.opportunity_code,
                "opportunity_name": opp.opportunity_name,
                "opportunity_stage": opp.opportunity_stage,
                "expected_contract_amount": float(opp.expected_contract_amount)
                if opp.expected_contract_amount
                else None,
                "sales_owner_name": owner_name,
                "channel_name": channel_name,
                "project_id": opp.project_id,
            }
        )

    projects_result = await db.execute(
        select(Project, User.name)
        .outerjoin(User, Project.sales_owner_id == User.id)
        .where(Project.terminal_customer_id == customer_id)
    )
    projects_rows = projects_result.all()
    projects = []
    for row in projects_rows:
        proj = row[0]
        owner_name = row[1]
        projects.append(
            {
                "id": proj.id,
                "project_code": proj.project_code,
                "project_name": proj.project_name,
                "project_status": proj.project_status,
                "business_type": proj.business_type,
                "downstream_contract_amount": float(proj.downstream_contract_amount)
                if proj.downstream_contract_amount
                else None,
                "sales_owner_name": owner_name,
            }
        )

    follow_ups_result = await db.execute(
        select(FollowUp, User.name)
        .outerjoin(User, FollowUp.follower_id == User.id)
        .where(FollowUp.terminal_customer_id == customer_id)
        .order_by(FollowUp.follow_up_date.desc())
        .limit(20)
    )
    fu_rows = follow_ups_result.all()
    follow_ups = []
    for row in fu_rows:
        fu = row[0]
        follower_name = row[1]
        follow_ups.append(
            {
                "id": fu.id,
                "follow_up_date": str(fu.follow_up_date) if fu.follow_up_date else None,
                "follow_up_method": fu.follow_up_method,
                "follow_up_content": fu.follow_up_content,
                "follow_up_conclusion": fu.follow_up_conclusion,
                "follower_name": follower_name,
            }
        )

    contracts_result = await db.execute(
        select(Contract).where(Contract.terminal_customer_id == customer_id)
    )
    contracts_rows = contracts_result.all()
    contracts = []
    for row in contracts_rows:
        c = row[0]
        contracts.append(
            {
                "id": c.id,
                "contract_code": c.contract_code,
                "contract_name": c.contract_name,
                "contract_direction": c.contract_direction,
                "contract_status": c.contract_status,
                "contract_amount": float(c.contract_amount)
                if c.contract_amount
                else None,
                "signing_date": str(c.signing_date) if c.signing_date else None,
            }
        )

    return CustomerFullView(
        customer={
            "id": customer.id,
            "customer_code": customer.customer_code,
            "customer_name": customer.customer_name,
            "credit_code": customer.credit_code,
            "customer_industry": customer.customer_industry,
            "customer_region": customer.customer_region,
            "customer_status": customer.customer_status,
            "main_contact": customer.main_contact,
            "phone": customer.phone,
            "notes": customer.notes,
            "customer_owner_name": customer.owner.name if customer.owner else None,
        },
        channel=channel_data,
        summary={
            "leads_count": len(leads),
            "opportunities_count": len(opportunities),
            "projects_count": len(projects),
            "follow_ups_count": len(follow_ups),
            "contracts_count": len(contracts),
        },
        leads=leads,
        opportunities=opportunities,
        projects=projects,
        follow_ups=follow_ups,
        contracts=contracts,
    )


@router.get("/customers/{customer_id}/finance-view", response_model=CustomerFinanceView)
async def get_customer_finance_view(
    customer_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.services.finance_view_service import finance_view_service

    user_role = current_user.get("role")
    if user_role not in ["admin", "finance"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="财务视图仅限管理员和财务角色访问",
        )

    finance_view = await finance_view_service.get_customer_finance_view(customer_id, db)
    if not finance_view:
        raise HTTPException(status_code=404, detail="客户不存在")

    return finance_view
