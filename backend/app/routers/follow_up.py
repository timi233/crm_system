from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database import get_db
from app.models.customer import TerminalCustomer
from app.models.followup import FollowUp
from app.models.lead import Lead
from app.models.opportunity import Opportunity
from app.models.project import Project
from app.models.user import User
from app.models.work_order import WorkOrder, WorkOrderTechnician
from app.schemas.follow_up import FollowUpCreate, FollowUpRead, FollowUpUpdate
from app.services.operation_log_service import log_create, log_delete, log_update


router = APIRouter(prefix="/follow-ups", tags=["follow-ups"])


def _parse_date(value: Optional[str]) -> Optional[date]:
    if not value:
        return None
    if isinstance(value, date):
        return value
    return date.fromisoformat(value)


async def _resolve_terminal_customer_id(
    db: AsyncSession,
    lead_id: Optional[int],
    opportunity_id: Optional[int],
    project_id: Optional[int],
) -> Optional[int]:
    if lead_id:
        lead = await db.get(Lead, lead_id)
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")
        return lead.terminal_customer_id

    if opportunity_id:
        opportunity = await db.get(Opportunity, opportunity_id)
        if not opportunity:
            raise HTTPException(status_code=404, detail="Opportunity not found")
        return opportunity.terminal_customer_id

    if project_id:
        project = await db.get(Project, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        return project.terminal_customer_id

    return None


async def _ensure_sales_follow_up_access(
    db: AsyncSession,
    user_id: int,
    *,
    follower_id: Optional[int] = None,
    lead_id: Optional[int] = None,
    opportunity_id: Optional[int] = None,
    project_id: Optional[int] = None,
    terminal_customer_id: Optional[int] = None,
):
    if follower_id == user_id:
        return

    if lead_id:
        lead = await db.get(Lead, lead_id)
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")
        if lead.sales_owner_id == user_id:
            return

    if opportunity_id:
        opportunity = await db.get(Opportunity, opportunity_id)
        if not opportunity:
            raise HTTPException(status_code=404, detail="Opportunity not found")
        if opportunity.sales_owner_id == user_id:
            return

    if project_id:
        project = await db.get(Project, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        if project.sales_owner_id == user_id:
            return

    if terminal_customer_id:
        customer = await db.get(TerminalCustomer, terminal_customer_id)
        if customer and customer.customer_owner_id == user_id:
            return

    raise HTTPException(status_code=403, detail="只能操作自己负责的跟进记录")


async def _ensure_can_write_follow_up(
    db: AsyncSession,
    current_user: dict,
    *,
    follower_id: Optional[int] = None,
    lead_id: Optional[int] = None,
    opportunity_id: Optional[int] = None,
    project_id: Optional[int] = None,
    terminal_customer_id: Optional[int] = None,
):
    role = current_user.get("role")
    user_id = current_user["id"]

    if role in {"admin", "business"}:
        return

    if role != "sales":
        raise HTTPException(status_code=403, detail="无权限修改跟进记录")

    await _ensure_sales_follow_up_access(
        db,
        user_id,
        follower_id=follower_id,
        lead_id=lead_id,
        opportunity_id=opportunity_id,
        project_id=project_id,
        terminal_customer_id=terminal_customer_id,
    )


@router.get("/", response_model=list[FollowUpRead])
async def list_follow_ups(
    terminal_customer_id: Optional[int] = None,
    lead_id: Optional[int] = None,
    opportunity_id: Optional[int] = None,
    project_id: Optional[int] = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    role = current_user.get("role")
    user_id = current_user["id"]

    query = (
        select(
            FollowUp,
            TerminalCustomer.customer_name,
            User.name,
            Lead.lead_name,
            Opportunity.opportunity_name,
            Project.project_name,
        )
        .outerjoin(TerminalCustomer, FollowUp.terminal_customer_id == TerminalCustomer.id)
        .outerjoin(User, FollowUp.follower_id == User.id)
        .outerjoin(Lead, FollowUp.lead_id == Lead.id)
        .outerjoin(Opportunity, FollowUp.opportunity_id == Opportunity.id)
        .outerjoin(Project, FollowUp.project_id == Project.id)
    )

    if role in {"admin", "business"}:
        pass
    elif role == "sales":
        owned_leads = select(Lead.id).where(Lead.sales_owner_id == user_id)
        owned_opportunities = select(Opportunity.id).where(
            Opportunity.sales_owner_id == user_id
        )
        owned_projects = select(Project.id).where(Project.sales_owner_id == user_id)
        owned_customers = select(TerminalCustomer.id).where(
            TerminalCustomer.customer_owner_id == user_id
        )
        query = query.where(
            or_(
                FollowUp.follower_id == user_id,
                FollowUp.lead_id.in_(owned_leads),
                FollowUp.opportunity_id.in_(owned_opportunities),
                FollowUp.project_id.in_(owned_projects),
                FollowUp.terminal_customer_id.in_(owned_customers),
            )
        )
    elif role == "technician":
        assigned_leads = (
            select(WorkOrder.lead_id)
            .join(
                WorkOrderTechnician,
                WorkOrderTechnician.work_order_id == WorkOrder.id,
            )
            .where(
                WorkOrderTechnician.technician_id == user_id,
                WorkOrder.lead_id.isnot(None),
            )
        )
        assigned_opportunities = (
            select(WorkOrder.opportunity_id)
            .join(
                WorkOrderTechnician,
                WorkOrderTechnician.work_order_id == WorkOrder.id,
            )
            .where(
                WorkOrderTechnician.technician_id == user_id,
                WorkOrder.opportunity_id.isnot(None),
            )
        )
        assigned_projects = (
            select(WorkOrder.project_id)
            .join(
                WorkOrderTechnician,
                WorkOrderTechnician.work_order_id == WorkOrder.id,
            )
            .where(
                WorkOrderTechnician.technician_id == user_id,
                WorkOrder.project_id.isnot(None),
            )
        )
        query = query.where(
            or_(
                FollowUp.lead_id.in_(assigned_leads),
                FollowUp.opportunity_id.in_(assigned_opportunities),
                FollowUp.project_id.in_(assigned_projects),
            )
        )
    else:
        raise HTTPException(status_code=403, detail="无权限访问跟进记录")

    if terminal_customer_id:
        query = query.where(FollowUp.terminal_customer_id == terminal_customer_id)
    if lead_id:
        query = query.where(FollowUp.lead_id == lead_id)
    if opportunity_id:
        query = query.where(FollowUp.opportunity_id == opportunity_id)
    if project_id:
        query = query.where(FollowUp.project_id == project_id)
    query = query.order_by(FollowUp.follow_up_date.desc())
    result = await db.execute(query)
    rows = result.all()

    follow_ups = []
    for row in rows:
        fu = row[0]
        customer_name = row[1] if len(row) > 1 else None
        follower_name = row[2] if len(row) > 2 else None
        lead_name = row[3] if len(row) > 3 else None
        opp_name = row[4] if len(row) > 4 else None
        proj_name = row[5] if len(row) > 5 else None
        follow_ups.append(
            FollowUpRead(
                id=fu.id,
                terminal_customer_id=fu.terminal_customer_id,
                lead_id=fu.lead_id,
                opportunity_id=fu.opportunity_id,
                project_id=fu.project_id,
                follow_up_date=fu.follow_up_date,
                follow_up_method=fu.follow_up_method,
                follow_up_content=fu.follow_up_content,
                follow_up_conclusion=fu.follow_up_conclusion,
                next_action=fu.next_action,
                next_follow_up_date=fu.next_follow_up_date,
                follower_id=fu.follower_id,
                created_at=fu.created_at,
                terminal_customer_name=customer_name,
                follower_name=follower_name,
                lead_name=lead_name,
                opportunity_name=opp_name,
                project_name=proj_name,
            )
        )
    return follow_ups


@router.post("/", response_model=FollowUpRead)
async def create_follow_up(
    follow_up: FollowUpCreate,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not follow_up.lead_id and not follow_up.opportunity_id and not follow_up.project_id:
        raise HTTPException(
            status_code=400,
            detail="关联线索、关联商机、关联项目至少需要选择一个",
        )

    terminal_customer_id = await _resolve_terminal_customer_id(
        db,
        follow_up.lead_id,
        follow_up.opportunity_id,
        follow_up.project_id,
    )
    await _ensure_can_write_follow_up(
        db,
        current_user,
        lead_id=follow_up.lead_id,
        opportunity_id=follow_up.opportunity_id,
        project_id=follow_up.project_id,
        terminal_customer_id=terminal_customer_id,
    )

    new_follow_up = FollowUp(
        terminal_customer_id=terminal_customer_id,
        lead_id=follow_up.lead_id,
        opportunity_id=follow_up.opportunity_id,
        project_id=follow_up.project_id,
        follow_up_date=_parse_date(follow_up.follow_up_date),
        follow_up_method=follow_up.follow_up_method,
        follow_up_content=follow_up.follow_up_content,
        follow_up_conclusion=follow_up.follow_up_conclusion,
        next_action=follow_up.next_action,
        next_follow_up_date=_parse_date(follow_up.next_follow_up_date),
        follower_id=current_user["id"],
        created_at=date.today(),
    )
    db.add(new_follow_up)
    await db.flush()
    await db.refresh(new_follow_up)

    related_entity = []
    if follow_up.lead_id:
        related_entity.append(f"线索#{follow_up.lead_id}")
    if follow_up.opportunity_id:
        related_entity.append(f"商机#{follow_up.opportunity_id}")
    if follow_up.project_id:
        related_entity.append(f"项目#{follow_up.project_id}")

    await log_create(
        db=db,
        user_id=current_user["id"],
        user_name=current_user["name"],
        entity_type="follow_up",
        entity_id=new_follow_up.id,
        entity_name=f"跟进记录#{new_follow_up.id}",
        description=f"创建跟进记录: {', '.join(related_entity) if related_entity else '独立跟进'}",
        ip_address=request.client.host if request.client else None,
    )

    await db.commit()
    await db.refresh(new_follow_up)

    customer_name = None
    follower_name = current_user["name"]
    lead_name = None
    opp_name = None
    proj_name = None

    if terminal_customer_id:
        result = await db.execute(
            select(TerminalCustomer.customer_name).where(
                TerminalCustomer.id == terminal_customer_id
            )
        )
        row = result.first()
        if row:
            customer_name = row[0]
    if follow_up.lead_id:
        result = await db.execute(select(Lead.lead_name).where(Lead.id == follow_up.lead_id))
        row = result.first()
        if row:
            lead_name = row[0]
    if follow_up.opportunity_id:
        result = await db.execute(
            select(Opportunity.opportunity_name).where(
                Opportunity.id == follow_up.opportunity_id
            )
        )
        row = result.first()
        if row:
            opp_name = row[0]
    if follow_up.project_id:
        result = await db.execute(
            select(Project.project_name).where(Project.id == follow_up.project_id)
        )
        row = result.first()
        if row:
            proj_name = row[0]

    return FollowUpRead(
        id=new_follow_up.id,
        terminal_customer_id=terminal_customer_id,
        lead_id=follow_up.lead_id,
        opportunity_id=follow_up.opportunity_id,
        project_id=follow_up.project_id,
        follow_up_date=new_follow_up.follow_up_date,
        follow_up_method=new_follow_up.follow_up_method,
        follow_up_content=new_follow_up.follow_up_content,
        follow_up_conclusion=new_follow_up.follow_up_conclusion,
        next_action=new_follow_up.next_action,
        next_follow_up_date=new_follow_up.next_follow_up_date,
        follower_id=current_user["id"],
        created_at=new_follow_up.created_at,
        terminal_customer_name=customer_name,
        follower_name=follower_name,
        lead_name=lead_name,
        opportunity_name=opp_name,
        project_name=proj_name,
    )


@router.put("/{follow_up_id}", response_model=FollowUpRead)
async def update_follow_up(
    follow_up_id: int,
    follow_up: FollowUpUpdate,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(FollowUp).where(FollowUp.id == follow_up_id))
    existing = result.scalar_one_or_none()
    if not existing:
        raise HTTPException(status_code=404, detail="FollowUp not found")

    update_data = follow_up.model_dump(exclude_unset=True)
    target_lead_id = update_data.get("lead_id", existing.lead_id)
    target_opportunity_id = update_data.get("opportunity_id", existing.opportunity_id)
    target_project_id = update_data.get("project_id", existing.project_id)

    target_terminal_customer_id = existing.terminal_customer_id
    if (
        "lead_id" in update_data
        or "opportunity_id" in update_data
        or "project_id" in update_data
    ):
        target_terminal_customer_id = await _resolve_terminal_customer_id(
            db,
            target_lead_id,
            target_opportunity_id,
            target_project_id,
        )

    await _ensure_can_write_follow_up(
        db,
        current_user,
        follower_id=existing.follower_id,
        lead_id=target_lead_id,
        opportunity_id=target_opportunity_id,
        project_id=target_project_id,
        terminal_customer_id=target_terminal_customer_id,
    )

    for field, value in update_data.items():
        if field in ["follow_up_date", "next_follow_up_date"]:
            value = _parse_date(value)
        setattr(existing, field, value)

    if (
        "lead_id" in update_data
        or "opportunity_id" in update_data
        or "project_id" in update_data
    ):
        existing.terminal_customer_id = target_terminal_customer_id

    await db.flush()

    await log_update(
        db=db,
        user_id=current_user["id"],
        user_name=current_user["name"],
        entity_type="follow_up",
        entity_id=existing.id,
        entity_name=f"跟进记录#{existing.id}",
        description=f"更新跟进记录#{existing.id}",
        ip_address=request.client.host if request.client else None,
    )

    await db.commit()
    await db.refresh(existing)

    customer_name = None
    follower_name = None
    lead_name = None
    opp_name = None
    proj_name = None

    if existing.terminal_customer_id:
        result = await db.execute(
            select(TerminalCustomer.customer_name).where(
                TerminalCustomer.id == existing.terminal_customer_id
            )
        )
        row = result.first()
        if row:
            customer_name = row[0]
    if existing.follower_id:
        result = await db.execute(select(User.name).where(User.id == existing.follower_id))
        row = result.first()
        if row:
            follower_name = row[0]
    if existing.lead_id:
        result = await db.execute(select(Lead.lead_name).where(Lead.id == existing.lead_id))
        row = result.first()
        if row:
            lead_name = row[0]
    if existing.opportunity_id:
        result = await db.execute(
            select(Opportunity.opportunity_name).where(
                Opportunity.id == existing.opportunity_id
            )
        )
        row = result.first()
        if row:
            opp_name = row[0]
    if existing.project_id:
        result = await db.execute(
            select(Project.project_name).where(Project.id == existing.project_id)
        )
        row = result.first()
        if row:
            proj_name = row[0]

    return FollowUpRead(
        id=existing.id,
        terminal_customer_id=existing.terminal_customer_id,
        lead_id=existing.lead_id,
        opportunity_id=existing.opportunity_id,
        project_id=existing.project_id,
        follow_up_date=existing.follow_up_date,
        follow_up_method=existing.follow_up_method,
        follow_up_content=existing.follow_up_content,
        follow_up_conclusion=existing.follow_up_conclusion,
        next_action=existing.next_action,
        next_follow_up_date=existing.next_follow_up_date,
        follower_id=existing.follower_id,
        created_at=existing.created_at,
        terminal_customer_name=customer_name,
        follower_name=follower_name,
        lead_name=lead_name,
        opportunity_name=opp_name,
        project_name=proj_name,
    )


@router.delete("/{follow_up_id}")
async def delete_follow_up(
    follow_up_id: int,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(FollowUp).where(FollowUp.id == follow_up_id))
    follow_up = result.scalar_one_or_none()
    if not follow_up:
        raise HTTPException(status_code=404, detail="FollowUp not found")

    await _ensure_can_write_follow_up(
        db,
        current_user,
        follower_id=follow_up.follower_id,
        lead_id=follow_up.lead_id,
        opportunity_id=follow_up.opportunity_id,
        project_id=follow_up.project_id,
        terminal_customer_id=follow_up.terminal_customer_id,
    )

    await log_delete(
        db=db,
        user_id=current_user["id"],
        user_name=current_user["name"],
        entity_type="follow_up",
        entity_id=follow_up.id,
        entity_name=f"跟进记录#{follow_up.id}",
        description=f"删除跟进记录#{follow_up.id}",
        ip_address=request.client.host if request.client else None,
    )

    await db.delete(follow_up)
    await db.commit()
    return {"message": "FollowUp deleted successfully"}
