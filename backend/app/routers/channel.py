from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from typing import List, Optional

from app.database import get_db
from app.core.dependencies import get_current_user
from app.core.channel_permissions import (
    apply_channel_scope_filter,
    assert_can_access_channel,
    require_channel_permission,
    require_channel_create,
    require_channel_delete,
    check_channel_exists,
)
from app.models.channel import Channel
from app.models.channel_contact import ChannelContact
from app.models.contract import Contract
from app.models.customer import TerminalCustomer
from app.models.customer_channel_link import CustomerChannelLink
from app.models.followup import FollowUp
from app.models.lead import Lead
from app.models.opportunity import Opportunity
from app.models.project import Project
from app.models.work_order import WorkOrder
from app.models.channel_assignment import ChannelAssignment
from app.models.execution_plan import ExecutionPlan
from app.models.unified_target import UnifiedTarget, TargetType
from app.models.user import User
from app.schemas.channel import ChannelCreate, ChannelFullView, ChannelRead, ChannelUpdate
from app.schemas.channel_contact import (
    ChannelContactCreate,
    ChannelContactRead,
    ChannelContactUpdate,
)
from app.services.auto_number_service import generate_code
from app.services.operation_log_service import log_create, log_update, log_delete
from app.services.channel_performance_service import refresh_channel_performance


router = APIRouter(prefix="/channels", tags=["channels"])


@router.get("/", response_model=List[ChannelRead])
async def list_channels(
    channel_type: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    stmt = select(Channel)
    if channel_type:
        stmt = stmt.where(Channel.channel_type == channel_type)
    if status:
        stmt = stmt.where(Channel.status == status)

    stmt = await apply_channel_scope_filter(stmt, Channel, current_user, db)

    stmt = stmt.order_by(Channel.id.desc())
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/", response_model=ChannelRead)
async def create_channel(
    channel: ChannelCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _: None = Depends(require_channel_create()),
):
    channel_code = await generate_code(db, "channel")
    new_channel = Channel(
        channel_code=channel_code,
        created_by=current_user.get("id"),
        **channel.model_dump(),
    )
    db.add(new_channel)
    await db.flush()
    await log_create(
        db=db,
        user_id=current_user.get("id", 0),
        user_name=current_user.get("name", ""),
        entity_type="channel",
        entity_id=new_channel.id,
        entity_name=new_channel.company_name,
        description=f"创建渠道: {new_channel.company_name}",
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    await db.refresh(new_channel)
    return new_channel


@router.get("/{channel_id}", response_model=ChannelRead)
async def get_channel(
    channel_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _: None = Depends(require_channel_permission("read")),
):
    result = await db.execute(select(Channel).where(Channel.id == channel_id))
    channel = result.scalar_one()
    return channel


@router.put("/{channel_id}", response_model=ChannelRead)
async def update_channel(
    channel_id: int,
    channel: ChannelUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _: None = Depends(require_channel_permission("write")),
):
    result = await db.execute(select(Channel).where(Channel.id == channel_id))
    existing = result.scalar_one()

    for field, value in channel.model_dump(exclude_unset=True).items():
        setattr(existing, field, value)
    existing.last_modified_by = current_user.get("id")

    await log_update(
        db=db,
        user_id=current_user.get("id", 0),
        user_name=current_user.get("name", ""),
        entity_type="channel",
        entity_id=existing.id,
        entity_name=existing.company_name,
        description=f"更新渠道: {existing.company_name}",
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    await db.refresh(existing)
    return existing


@router.delete("/{channel_id}")
async def delete_channel(
    channel_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _: None = Depends(require_channel_delete()),
):
    result = await db.execute(select(Channel).where(Channel.id == channel_id))
    channel = result.scalar_one()

    company_name = channel.company_name
    await log_delete(
        db=db,
        user_id=current_user.get("id", 0),
        user_name=current_user.get("name", ""),
        entity_type="channel",
        entity_id=channel_id,
        entity_name=company_name,
        description=f"删除渠道: {company_name}",
        ip_address=request.client.host if request.client else None,
    )
    await db.delete(channel)
    await db.commit()
    return {"message": "Channel deleted successfully"}


@router.get("/check-credit-code")
async def check_channel_credit_code(
    credit_code: str,
    exclude_id: Optional[int] = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Channel).where(Channel.credit_code == credit_code)
    if exclude_id:
        query = query.where(Channel.id != exclude_id)
    result = await db.execute(query)
    existing = result.scalar_one_or_none()
    return {"exists": existing is not None}


@router.get("/{channel_id}/full-view", response_model=ChannelFullView)
async def get_channel_full_view(
    channel_id: int,
    year: Optional[int] = Query(None, description="过滤年份"),
    quarter: Optional[int] = Query(None, ge=1, le=4, description="过滤季度"),
    active_only: bool = Query(True, description="只显示活跃记录"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await assert_can_access_channel(db, current_user, channel_id, "read")

    result = await db.execute(select(Channel).where(Channel.id == channel_id))
    channel = result.scalar_one_or_none()
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")

    customers_result = await db.execute(
        select(TerminalCustomer, User.name)
        .outerjoin(User, TerminalCustomer.customer_owner_id == User.id)
        .where(
            or_(
                TerminalCustomer.channel_id == channel_id,
                TerminalCustomer.id.in_(
                    select(CustomerChannelLink.customer_id).where(
                        CustomerChannelLink.channel_id == channel_id
                    )
                ),
            )
        )
    )
    customers = []
    for row in customers_result.all():
        customer = row[0]
        owner_name = row[1]
        customers.append(
            {
                "id": customer.id,
                "customer_code": customer.customer_code,
                "customer_name": customer.customer_name,
                "customer_industry": customer.customer_industry,
                "customer_region": customer.customer_region,
                "customer_status": customer.customer_status,
                "customer_owner_name": owner_name,
            }
        )

    opps_result = await db.execute(
        select(Opportunity, TerminalCustomer.customer_name, User.name)
        .outerjoin(TerminalCustomer, Opportunity.terminal_customer_id == TerminalCustomer.id)
        .outerjoin(User, Opportunity.sales_owner_id == User.id)
        .where(Opportunity.channel_id == channel_id)
    )
    opportunities = []
    for row in opps_result.all():
        opp = row[0]
        opportunities.append(
            {
                "id": opp.id,
                "opportunity_code": opp.opportunity_code,
                "opportunity_name": opp.opportunity_name,
                "opportunity_stage": opp.opportunity_stage,
                "expected_contract_amount": float(opp.expected_contract_amount)
                if opp.expected_contract_amount
                else None,
                "terminal_customer_name": row[1],
                "sales_owner_name": row[2],
                "project_id": opp.project_id,
            }
        )

    projects_result = await db.execute(
        select(Project, TerminalCustomer.customer_name, User.name)
        .outerjoin(TerminalCustomer, Project.terminal_customer_id == TerminalCustomer.id)
        .outerjoin(User, Project.sales_owner_id == User.id)
        .where(Project.channel_id == channel_id)
    )
    projects = []
    for row in projects_result.all():
        project = row[0]
        projects.append(
            {
                "id": project.id,
                "project_code": project.project_code,
                "project_name": project.project_name,
                "project_status": project.project_status,
                "business_type": project.business_type,
                "downstream_contract_amount": float(project.downstream_contract_amount)
                if project.downstream_contract_amount
                else None,
                "terminal_customer_name": row[1],
                "sales_owner_name": row[2],
            }
        )

    contracts_result = await db.execute(select(Contract).where(Contract.channel_id == channel_id))
    contracts = []
    for row in contracts_result.all():
        contract = row[0]
        contracts.append(
            {
                "id": contract.id,
                "contract_code": contract.contract_code,
                "contract_name": contract.contract_name,
                "contract_direction": contract.contract_direction,
                "contract_status": contract.contract_status,
                "contract_amount": float(contract.contract_amount)
                if contract.contract_amount
                else None,
                "signing_date": str(contract.signing_date) if contract.signing_date else None,
            }
        )

    work_orders_result = await db.execute(select(WorkOrder).where(WorkOrder.channel_id == channel_id))
    work_orders = []
    for row in work_orders_result.all():
        work_order = row[0]
        work_orders.append(
            {
                "id": work_order.id,
                "work_order_no": work_order.work_order_no,
                "order_type": work_order.order_type.value if work_order.order_type else None,
                "status": work_order.status.value if work_order.status else None,
                "description": work_order.description,
                "customer_name": work_order.customer_name,
            }
        )

    assignments_result = await db.execute(
        select(ChannelAssignment, User.name)
        .outerjoin(User, ChannelAssignment.user_id == User.id)
        .where(ChannelAssignment.channel_id == channel_id)
    )
    assignments = []
    for row in assignments_result.all():
        assignment = row[0]
        assignments.append(
            {
                "id": assignment.id,
                "user_id": assignment.user_id,
                "user_name": row[1],
                "permission_level": assignment.permission_level.value
                if assignment.permission_level
                else None,
                "assigned_at": str(assignment.assigned_at) if assignment.assigned_at else None,
            }
        )

    execution_plans_query = (
        select(ExecutionPlan, User.name)
        .outerjoin(User, ExecutionPlan.user_id == User.id)
        .where(ExecutionPlan.channel_id == channel_id)
    )
    if active_only:
        execution_plans_query = execution_plans_query.where(
            ExecutionPlan.status.in_(["in-progress", "planned"])
        )
    execution_plans_result = await db.execute(execution_plans_query)
    execution_plans = []
    for row in execution_plans_result.all():
        plan = row[0]
        execution_plans.append(
            {
                "id": plan.id,
                "plan_type": plan.plan_type.value if plan.plan_type else None,
                "plan_period": plan.plan_period,
                "plan_content": plan.plan_content,
                "status": plan.status.value if plan.status else None,
            }
        )

    targets_query = select(UnifiedTarget).where(UnifiedTarget.channel_id == channel_id)
    if year is not None:
        targets_query = targets_query.where(UnifiedTarget.year == year)
    if quarter is not None:
        targets_query = targets_query.where(UnifiedTarget.quarter == quarter)
    targets_result = await db.execute(targets_query)
    targets = []
    for row in targets_result.all():
        target = row[0]
        targets.append(
            {
                "id": target.id,
                "year": target.year,
                "quarter": target.quarter,
                "month": target.month,
                "performance_target": float(target.performance_target)
                if target.performance_target
                else None,
                "achieved_performance": float(target.achieved_performance)
                if target.achieved_performance
                else None,
            }
        )

    return ChannelFullView(
        channel={
            "id": channel.id,
            "channel_code": channel.channel_code,
            "company_name": channel.company_name,
            "channel_type": channel.channel_type,
            "status": channel.status,
            "main_contact": channel.main_contact,
            "phone": channel.phone,
            "email": channel.email,
            "province": channel.province,
            "city": channel.city,
            "address": channel.address,
            "credit_code": channel.credit_code,
            "website": channel.website,
            "wechat": channel.wechat,
            "cooperation_region": channel.cooperation_region,
            "discount_rate": float(channel.discount_rate) if channel.discount_rate else None,
            "notes": channel.notes,
        },
        summary={
            "customers_count": len(customers),
            "opportunities_count": len(opportunities),
            "projects_count": len(projects),
            "contracts_count": len(contracts),
            "work_orders_count": len(work_orders),
            "assignments_count": len(assignments),
            "execution_plans_count": len(execution_plans),
            "targets_count": len(targets),
            "total_contract_amount": sum(c.get("contract_amount", 0) or 0 for c in contracts),
            "active_plans_count": len(
                [plan for plan in execution_plans if plan["status"] in ["in-progress", "planned"]]
            ),
        },
        customers=customers,
        opportunities=opportunities,
        projects=projects,
        contracts=contracts,
        work_orders=work_orders,
        assignments=assignments,
        execution_plans=execution_plans,
        targets=targets,
    )


@router.get("/{channel_id}/work-orders")
async def list_channel_work_orders(
    channel_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    _: None = Depends(require_channel_permission("read")),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(WorkOrder).where(WorkOrder.channel_id == channel_id)
    stmt = stmt.offset(skip).limit(limit)

    result = await db.execute(stmt)
    work_orders = result.scalars().all()

    count_stmt = (
        select(func.count())
        .select_from(WorkOrder)
        .where(WorkOrder.channel_id == channel_id)
    )
    count_result = await db.execute(count_stmt)
    total = count_result.scalar()

    return {"total": total, "items": work_orders}


@router.get("/{channel_id}/assignments")
async def list_channel_assignments(
    channel_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    _: None = Depends(require_channel_permission("read")),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(ChannelAssignment, User.name)
        .join(User, ChannelAssignment.user_id == User.id)
        .where(ChannelAssignment.channel_id == channel_id)
        .offset(skip)
        .limit(limit)
    )

    result = await db.execute(stmt)
    assignments = []
    for assignment, user_name in result.all():
        assignment_dict = {
            "id": assignment.id,
            "user_id": assignment.user_id,
            "user_name": user_name,
            "permission_level": assignment.permission_level,
            "assigned_at": assignment.assigned_at,
        }
        assignments.append(assignment_dict)

    count_stmt = (
        select(func.count())
        .select_from(ChannelAssignment)
        .where(ChannelAssignment.channel_id == channel_id)
    )
    count_result = await db.execute(count_stmt)
    total = count_result.scalar()

    return {"total": total, "items": assignments}


@router.get("/{channel_id}/execution-plans")
async def list_channel_execution_plans(
    channel_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    _: None = Depends(require_channel_permission("read")),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(ExecutionPlan).where(ExecutionPlan.channel_id == channel_id)
    stmt = stmt.offset(skip).limit(limit)

    result = await db.execute(stmt)
    execution_plans = result.scalars().all()

    count_stmt = (
        select(func.count())
        .select_from(ExecutionPlan)
        .where(ExecutionPlan.channel_id == channel_id)
    )
    count_result = await db.execute(count_stmt)
    total = count_result.scalar()

    return {"total": total, "items": execution_plans}


@router.get("/{channel_id}/targets")
async def list_channel_targets(
    channel_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    _: None = Depends(require_channel_permission("read")),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(UnifiedTarget).where(
        UnifiedTarget.channel_id == channel_id,
        UnifiedTarget.target_type == TargetType.channel,
    )
    stmt = stmt.offset(skip).limit(limit)

    result = await db.execute(stmt)
    targets = result.scalars().all()

    count_stmt = (
        select(func.count())
        .select_from(UnifiedTarget)
        .where(
            UnifiedTarget.channel_id == channel_id,
            UnifiedTarget.target_type == TargetType.channel,
        )
    )
    count_result = await db.execute(count_stmt)
    total = count_result.scalar()

    return {"total": total, "items": targets}


@router.get("/{channel_id}/follow-ups")
async def list_channel_follow_ups(
    channel_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    _: None = Depends(require_channel_permission("read")),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(
            FollowUp,
            User.name,
            Lead.lead_name,
            Opportunity.opportunity_name,
            Project.project_name,
        )
        .outerjoin(User, FollowUp.follower_id == User.id)
        .outerjoin(Lead, FollowUp.lead_id == Lead.id)
        .outerjoin(Opportunity, FollowUp.opportunity_id == Opportunity.id)
        .outerjoin(Project, FollowUp.project_id == Project.id)
        .where(FollowUp.channel_id == channel_id)
        .order_by(FollowUp.follow_up_date.desc(), FollowUp.id.desc())
        .offset(skip)
        .limit(limit)
    )

    result = await db.execute(stmt)
    items = []
    for follow_up, follower_name, lead_name, opportunity_name, project_name in result.all():
        items.append(
            {
                "id": follow_up.id,
                "channel_id": follow_up.channel_id,
                "follow_up_date": follow_up.follow_up_date,
                "follow_up_method": follow_up.follow_up_method,
                "follow_up_content": follow_up.follow_up_content,
                "follow_up_conclusion": follow_up.follow_up_conclusion,
                "next_action": follow_up.next_action,
                "next_follow_up_date": follow_up.next_follow_up_date,
                "follower_id": follow_up.follower_id,
                "follower_name": follower_name,
                "lead_id": follow_up.lead_id,
                "lead_name": lead_name,
                "opportunity_id": follow_up.opportunity_id,
                "opportunity_name": opportunity_name,
                "project_id": follow_up.project_id,
                "project_name": project_name,
                "created_at": follow_up.created_at,
            }
        )

    total = (
        await db.execute(
            select(func.count())
            .select_from(FollowUp)
            .where(FollowUp.channel_id == channel_id)
        )
    ).scalar()

    return {"total": total, "items": items}


@router.get("/{channel_id}/leads")
async def list_channel_leads(
    channel_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    _: None = Depends(require_channel_permission("read")),
    db: AsyncSession = Depends(get_db),
):
    lead_filter = or_(Lead.channel_id == channel_id, Lead.source_channel_id == channel_id)

    stmt = (
        select(Lead, User.name)
        .outerjoin(User, Lead.sales_owner_id == User.id)
        .where(lead_filter)
        .order_by(Lead.created_at.desc(), Lead.id.desc())
        .offset(skip)
        .limit(limit)
    )

    result = await db.execute(stmt)
    items = []
    for lead, sales_owner_name in result.all():
        items.append(
            {
                "id": lead.id,
                "lead_code": lead.lead_code,
                "lead_name": lead.lead_name,
                "stage": lead.lead_stage,
                "contact_person": lead.contact_person,
                "sales_owner_name": sales_owner_name,
                "created_at": lead.created_at,
            }
        )

    total = (
        await db.execute(select(func.count()).select_from(Lead).where(lead_filter))
    ).scalar()
    return {"total": total, "items": items}


async def _ensure_single_primary_contact(
    db: AsyncSession, channel_id: int, contact_id_to_keep: Optional[int] = None
):
    stmt = select(ChannelContact).where(ChannelContact.channel_id == channel_id)
    if contact_id_to_keep is not None:
        stmt = stmt.where(ChannelContact.id != contact_id_to_keep)
    result = await db.execute(stmt)
    for contact in result.scalars().all():
        contact.is_primary = False


@router.get("/{channel_id}/contacts", response_model=list[ChannelContactRead])
async def list_channel_contacts(
    channel_id: int,
    current_user: dict = Depends(get_current_user),
    _: None = Depends(require_channel_permission("read")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ChannelContact)
        .where(ChannelContact.channel_id == channel_id)
        .order_by(ChannelContact.is_primary.desc(), ChannelContact.id.asc())
    )
    return result.scalars().all()


@router.post("/{channel_id}/contacts", response_model=ChannelContactRead)
async def create_channel_contact(
    channel_id: int,
    payload: ChannelContactCreate,
    current_user: dict = Depends(get_current_user),
    _: None = Depends(require_channel_permission("write")),
    db: AsyncSession = Depends(get_db),
):
    await check_channel_exists(db, channel_id)

    if payload.is_primary:
        await _ensure_single_primary_contact(db, channel_id)

    contact = ChannelContact(channel_id=channel_id, **payload.model_dump())
    db.add(contact)
    await db.commit()
    await db.refresh(contact)
    return contact


@router.put("/{channel_id}/contacts/{contact_id}", response_model=ChannelContactRead)
async def update_channel_contact(
    channel_id: int,
    contact_id: int,
    payload: ChannelContactUpdate,
    current_user: dict = Depends(get_current_user),
    _: None = Depends(require_channel_permission("write")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ChannelContact).where(
            ChannelContact.id == contact_id, ChannelContact.channel_id == channel_id
        )
    )
    contact = result.scalar_one_or_none()
    if not contact:
        raise HTTPException(status_code=404, detail="Channel contact not found")

    update_data = payload.model_dump(exclude_unset=True)
    if update_data.get("is_primary") is True:
        await _ensure_single_primary_contact(db, channel_id, contact_id_to_keep=contact.id)

    for field, value in update_data.items():
        setattr(contact, field, value)

    await db.commit()
    await db.refresh(contact)
    return contact


@router.delete("/{channel_id}/contacts/{contact_id}")
async def delete_channel_contact(
    channel_id: int,
    contact_id: int,
    current_user: dict = Depends(get_current_user),
    _: None = Depends(require_channel_permission("write")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ChannelContact).where(
            ChannelContact.id == contact_id, ChannelContact.channel_id == channel_id
        )
    )
    contact = result.scalar_one_or_none()
    if not contact:
        raise HTTPException(status_code=404, detail="Channel contact not found")

    await db.delete(contact)
    await db.commit()
    return {"message": "Channel contact deleted successfully"}


@router.post("/{channel_id}/refresh-performance")
async def refresh_channel_performance_endpoint(
    channel_id: int,
    current_user: dict = Depends(get_current_user),
    _: None = Depends(require_channel_permission("write")),
    db: AsyncSession = Depends(get_db),
):
    await refresh_channel_performance(db, channel_id)
    return {"message": "Channel performance refreshed"}
