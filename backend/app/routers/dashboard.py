from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.dependencies import get_current_user
from app.database import get_db
from app.models.contract import Contract
from app.models.followup import FollowUp
from app.models.lead import Lead
from app.models.opportunity import Opportunity
from app.models.project import Project
from app.models.sales_target import SalesTarget
from app.models.user import User
from app.models.user_notification_read import UserNotificationRead
from app.schemas.dashboard import (
    DashboardFollowUpItem,
    DashboardNotificationItem,
    DashboardSummaryResponse,
    DashboardTodoItem,
    MarkNotificationsReadRequest,
    TeamRankItem,
)


router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummaryResponse)
async def get_dashboard_summary(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_id = current_user["id"]
    is_admin = current_user["role"] == "admin"

    lead_query = select(Lead)
    if not is_admin:
        lead_query = lead_query.where(Lead.sales_owner_id == user_id)
    lead_result = await db.execute(lead_query)
    leads = lead_result.scalars().all()

    opp_query = select(Opportunity)
    if not is_admin:
        opp_query = opp_query.where(Opportunity.sales_owner_id == user_id)
    opp_result = await db.execute(opp_query)
    opportunities = opp_result.scalars().all()

    project_query = select(Project)
    if not is_admin:
        project_query = project_query.where(Project.sales_owner_id == user_id)
    project_result = await db.execute(project_query)
    projects = project_result.scalars().all()

    contract_query = (
        select(Contract)
        .join(Project, Contract.project_id == Project.id)
        .where(Contract.contract_direction == "Downstream")
    )
    if not is_admin:
        contract_query = contract_query.where(Project.sales_owner_id == user_id)
    contract_result = await db.execute(contract_query)
    contracts = contract_result.scalars().all()

    today = date.today()
    month_start = today.replace(day=1)
    quarter = (today.month - 1) // 3 + 1
    quarter_start_month = (quarter - 1) * 3 + 1
    quarter_start = today.replace(month=quarter_start_month, day=1)

    month_contract_query = (
        select(Contract)
        .join(Project, Contract.project_id == Project.id)
        .where(Contract.contract_direction == "Downstream")
        .where(Contract.signing_date >= month_start)
    )
    if not is_admin:
        month_contract_query = month_contract_query.where(Project.sales_owner_id == user_id)
    month_contract_result = await db.execute(month_contract_query)
    month_contracts = month_contract_result.scalars().all()
    monthly_achieved = sum(float(c.contract_amount or 0) for c in month_contracts)

    quarter_contract_query = (
        select(Contract)
        .join(Project, Contract.project_id == Project.id)
        .where(Contract.contract_direction == "Downstream")
        .where(Contract.signing_date >= quarter_start)
    )
    if not is_admin:
        quarter_contract_query = quarter_contract_query.where(
            Project.sales_owner_id == user_id
        )
    quarter_contract_result = await db.execute(quarter_contract_query)
    quarter_contracts = quarter_contract_result.scalars().all()
    quarterly_achieved = sum(float(c.contract_amount or 0) for c in quarter_contracts)

    target_query = select(SalesTarget).where(
        SalesTarget.target_year == today.year,
        SalesTarget.target_type == "monthly",
        SalesTarget.target_period == today.month,
    )
    if not is_admin:
        target_query = target_query.where(SalesTarget.user_id == user_id)
    target_result = await db.execute(target_query)
    monthly_targets = target_result.scalars().all()
    monthly_target = sum(float(t.target_amount or 0) for t in monthly_targets)

    qtarget_query = select(SalesTarget).where(
        SalesTarget.target_year == today.year,
        SalesTarget.target_type == "quarterly",
        SalesTarget.target_period == quarter,
    )
    if not is_admin:
        qtarget_query = qtarget_query.where(SalesTarget.user_id == user_id)
    qtarget_result = await db.execute(qtarget_query)
    quarterly_targets = qtarget_result.scalars().all()
    quarterly_target = sum(float(t.target_amount or 0) for t in quarterly_targets)

    quarter_end_month = quarter_start_month + 2
    quarter_end = today.replace(month=quarter_end_month, day=28)
    forecast_query = select(Opportunity).where(
        Opportunity.opportunity_stage.notin_(["已成交", "已流失"]),
        Opportunity.expected_close_date >= quarter_start,
        Opportunity.expected_close_date <= quarter_end,
        Opportunity.expected_contract_amount != None,
    )
    if not is_admin:
        forecast_query = forecast_query.where(Opportunity.sales_owner_id == user_id)
    forecast_result = await db.execute(forecast_query)
    forecast_opps = forecast_result.scalars().all()
    quarterly_forecast_amount = sum(float(o.expected_contract_amount or 0) for o in forecast_opps)

    followup_query = select(FollowUp)
    if not is_admin:
        followup_query = followup_query.where(FollowUp.follower_id == user_id)
    followup_result = await db.execute(followup_query)
    followups = followup_result.scalars().all()
    pending_followups = sum(1 for f in followups if not f.next_action)

    won_count = sum(1 for o in opportunities if o.opportunity_stage == "已成交")
    lost_count = sum(1 for o in opportunities if o.opportunity_stage == "已流失")

    stalled_query = select(Opportunity).where(
        Opportunity.opportunity_stage.notin_(["已成交", "已流失"])
    )
    if not is_admin:
        stalled_query = stalled_query.where(Opportunity.sales_owner_id == user_id)
    stalled_result = await db.execute(stalled_query)
    stalled_opps = stalled_result.scalars().all()
    alerts_count = pending_followups + len(stalled_opps)

    last_month = today - timedelta(days=1)
    last_month_start = last_month.replace(day=1)
    last_month_leads = sum(1 for l in leads if l.created_at and l.created_at >= last_month_start)
    last_month_opps = sum(
        1 for o in opportunities if o.created_at and o.created_at >= last_month_start
    )

    last_month_target_result = await db.execute(
        select(SalesTarget).where(
            SalesTarget.target_year == last_month.year,
            SalesTarget.target_type == "monthly",
            SalesTarget.target_period == last_month.month,
        )
    )
    last_month_targets = last_month_target_result.scalars().all()
    monthly_target_prev = sum(float(t.target_amount or 0) for t in last_month_targets)

    last_month_contract_query = (
        select(Contract)
        .join(Project, Contract.project_id == Project.id)
        .where(Contract.contract_direction == "Downstream")
        .where(Contract.signing_date >= last_month_start)
        .where(Contract.signing_date <= last_month)
    )
    if not is_admin:
        last_month_contract_query = last_month_contract_query.where(
            Project.sales_owner_id == user_id
        )
    last_month_contract_result = await db.execute(last_month_contract_query)
    last_month_contracts = last_month_contract_result.scalars().all()
    monthly_achieved_prev = sum(float(c.contract_amount or 0) for c in last_month_contracts)

    last_quarter = (quarter - 1) if quarter > 1 else 4
    last_quarter_year = today.year if quarter > 1 else today.year - 1
    last_quarter_start = last_quarter_start_month = (last_quarter - 1) * 3 + 1
    last_quarter_start_date = today.replace(
        year=last_quarter_year,
        month=last_quarter_start_month,
        day=1,
    )
    last_quarter_end = last_quarter_start_date.replace(month=last_quarter_start_month + 2, day=28)

    last_qtarget_result = await db.execute(
        select(SalesTarget).where(
            SalesTarget.target_year == last_quarter_year,
            SalesTarget.target_type == "quarterly",
            SalesTarget.target_period == last_quarter,
        )
    )
    last_quarter_targets = last_qtarget_result.scalars().all()
    quarterly_target_prev = sum(float(t.target_amount or 0) for t in last_quarter_targets)

    last_quarter_contract_query = (
        select(Contract)
        .join(Project, Contract.project_id == Project.id)
        .where(Contract.contract_direction == "Downstream")
        .where(Contract.signing_date >= last_quarter_start_date)
        .where(Contract.signing_date <= last_quarter_end)
    )
    if not is_admin:
        last_quarter_contract_query = last_quarter_contract_query.where(
            Project.sales_owner_id == user_id
        )
    last_quarter_contract_result = await db.execute(last_quarter_contract_query)
    last_quarter_contracts = last_quarter_contract_result.scalars().all()
    quarterly_achieved_prev = sum(float(c.contract_amount or 0) for c in last_quarter_contracts)

    return DashboardSummaryResponse(
        leads_count=len(leads),
        opportunities_count=len(opportunities),
        projects_count=len(projects),
        contracts_count=len(contracts),
        pending_followups=pending_followups,
        alerts_count=alerts_count,
        won_opportunities=won_count,
        lost_opportunities=lost_count,
        quarterly_target=quarterly_target,
        quarterly_achieved=quarterly_achieved,
        monthly_target=monthly_target,
        monthly_achieved=monthly_achieved,
        quarterly_forecast_amount=quarterly_forecast_amount,
        monthly_target_prev=monthly_target_prev if monthly_target_prev > 0 else None,
        monthly_achieved_prev=monthly_achieved_prev if monthly_achieved_prev > 0 else None,
        quarterly_target_prev=quarterly_target_prev if quarterly_target_prev > 0 else None,
        quarterly_achieved_prev=quarterly_achieved_prev if quarterly_achieved_prev > 0 else None,
        leads_count_prev=last_month_leads,
        opportunities_count_prev=last_month_opps,
    )


@router.get("/todos", response_model=list[DashboardTodoItem])
async def get_dashboard_todos(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_id = current_user["id"]
    is_admin = current_user["role"] == "admin"
    today = date.today()
    todos = []

    followup_query = (
        select(FollowUp)
        .options(selectinload(FollowUp.terminal_customer))
        .where(FollowUp.follow_up_date >= today)
    )
    if not is_admin:
        followup_query = followup_query.where(FollowUp.follower_id == user_id)
    followup_query = followup_query.order_by(FollowUp.follow_up_date).limit(10)
    followup_result = await db.execute(followup_query)
    followups = followup_result.scalars().all()

    for followup in followups:
        entity_type = ""
        entity_id = 0
        if followup.lead_id:
            entity_type = "lead"
            entity_id = followup.lead_id
        elif followup.opportunity_id:
            entity_type = "opportunity"
            entity_id = followup.opportunity_id
        elif followup.project_id:
            entity_type = "project"
            entity_id = followup.project_id

        customer_name = followup.terminal_customer.customer_name if followup.terminal_customer else ""
        todos.append(
            DashboardTodoItem(
                id=followup.id,
                type="跟进提醒",
                title=followup.follow_up_content[:50] if followup.follow_up_content else "跟进任务",
                customer_name=customer_name,
                due_date=str(followup.follow_up_date) if followup.follow_up_date else None,
                priority="高" if followup.follow_up_date and followup.follow_up_date <= today else "中",
                entity_type=entity_type,
                entity_id=entity_id,
            )
        )

    return todos


@router.get("/recent-followups", response_model=list[DashboardFollowUpItem])
async def get_dashboard_recent_followups(
    limit: int = 5,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_id = current_user["id"]
    is_admin = current_user["role"] == "admin"

    followup_query = (
        select(FollowUp)
        .options(selectinload(FollowUp.terminal_customer), selectinload(FollowUp.follower))
        .order_by(FollowUp.follow_up_date.desc())
        .limit(limit)
    )
    if not is_admin:
        followup_query = followup_query.where(FollowUp.follower_id == user_id)
    followup_result = await db.execute(followup_query)
    followups = followup_result.scalars().all()

    items = []
    for followup in followups:
        entity_type = ""
        entity_id = 0
        if followup.lead_id:
            entity_type = "lead"
            entity_id = followup.lead_id
        elif followup.opportunity_id:
            entity_type = "opportunity"
            entity_id = followup.opportunity_id
        elif followup.project_id:
            entity_type = "project"
            entity_id = followup.project_id

        customer_name = followup.terminal_customer.customer_name if followup.terminal_customer else ""
        follower_name = followup.follower.name if followup.follower else ""
        items.append(
            DashboardFollowUpItem(
                id=followup.id,
                customer_name=customer_name,
                follow_up_date=str(followup.follow_up_date) if followup.follow_up_date else "",
                follow_up_method=followup.follow_up_method or "",
                follow_up_content=followup.follow_up_content[:100] if followup.follow_up_content else "",
                follower_name=follower_name,
                entity_type=entity_type,
                entity_id=entity_id,
            )
        )

    return items


@router.get("/notifications", response_model=list[DashboardNotificationItem])
async def get_dashboard_notifications(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return []


@router.get("/team-rank", response_model=list[TeamRankItem])
async def get_team_rank(
    limit: int = 5,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")

    today = date.today()
    month_start = today.replace(day=1)
    users_result = await db.execute(select(User).where(User.role == "sales"))
    users = users_result.scalars().all()

    user_stats = []
    for user in users:
        contract_query = (
            select(Contract)
            .join(Project, Contract.project_id == Project.id)
            .where(Contract.contract_direction == "Downstream")
            .where(Contract.signing_date >= month_start)
            .where(Project.sales_owner_id == user.id)
        )
        contract_result = await db.execute(contract_query)
        contracts = contract_result.scalars().all()
        total_amount = sum(float(c.contract_amount or 0) for c in contracts)
        user_stats.append(
            {
                "user_id": user.id,
                "user_name": user.name or f"用户{user.id}",
                "amount": total_amount,
            }
        )

    user_stats.sort(key=lambda item: item["amount"], reverse=True)
    result = []
    for index, stat in enumerate(user_stats[:limit]):
        result.append(
            TeamRankItem(
                rank=index + 1,
                user_id=stat["user_id"],
                user_name=stat["user_name"],
                amount=stat["amount"],
            )
        )
    return result


@router.post("/notifications/mark-read")
async def mark_notifications_read(
    request: MarkNotificationsReadRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_id = current_user["id"]
    now = datetime.utcnow()

    for item in request.notifications:
        if item.get("entity_type") and item.get("entity_id") and item.get("type"):
            existing = await db.execute(
                select(UserNotificationRead).where(
                    UserNotificationRead.user_id == user_id,
                    UserNotificationRead.entity_type == item["entity_type"],
                    UserNotificationRead.entity_id == item["entity_id"],
                    UserNotificationRead.notification_type == item["type"],
                )
            )
            if existing.scalars().first():
                continue

            read_record = UserNotificationRead(
                user_id=user_id,
                entity_type=item["entity_type"],
                entity_id=item["entity_id"],
                notification_type=item["type"],
                created_at=now,
            )
            db.add(read_record)

    await db.commit()
    return {"success": True}
