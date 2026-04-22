from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.core.policy import policy_service, build_principal
from app.models.channel import Channel
from app.database import get_db
from app.models.customer import TerminalCustomer
from app.models.followup import FollowUp
from app.models.lead import Lead
from app.models.opportunity import Opportunity
from app.models.project import Project
from app.models.user import User
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


def _infer_follow_up_type(
    lead_id: Optional[int],
    opportunity_id: Optional[int],
    project_id: Optional[int],
    channel_id: Optional[int],
    specified_type: Optional[str] = None,
) -> str:
    """推断跟进记录类型"""
    if specified_type in {"business", "channel"}:
        return specified_type

    # 如果只关联了渠道ID，认为是渠道跟进
    if channel_id is not None and all(
        x is None for x in [lead_id, opportunity_id, project_id]
    ):
        return "channel"

    # 如果关联了业务实体，认为是业务跟进
    if (
        any(x is not None for x in [lead_id, opportunity_id, project_id])
        and channel_id is None
    ):
        return "business"

    # 混合场景（同时关联业务和渠道），默认业务跟进
    return "business"


def _validate_follow_up_fields(
    follow_up_type: str, follow_up_conclusion: Optional[str]
):
    """根据跟进类型验证字段约束"""
    if follow_up_type not in {"business", "channel"}:
        raise HTTPException(status_code=400, detail="无效的跟进类型")
    if follow_up_type == "business":
        if not follow_up_conclusion:
            raise HTTPException(status_code=400, detail="业务跟进必须填写跟进结论")


def _build_follow_up_read(
    fu: FollowUp,
    customer_name: Optional[str],
    follower_name: Optional[str],
    lead_name: Optional[str],
    opportunity_name: Optional[str],
    project_name: Optional[str],
    channel_name: Optional[str],
) -> FollowUpRead:
    return FollowUpRead(
        id=fu.id,
        terminal_customer_id=fu.terminal_customer_id,
        lead_id=fu.lead_id,
        opportunity_id=fu.opportunity_id,
        project_id=fu.project_id,
        channel_id=fu.channel_id,
        follow_up_type=fu.follow_up_type,
        follow_up_date=fu.follow_up_date,
        follow_up_method=fu.follow_up_method,
        follow_up_content=fu.follow_up_content,
        follow_up_conclusion=fu.follow_up_conclusion,
        next_action=fu.next_action,
        next_follow_up_date=fu.next_follow_up_date,
        visit_location=fu.visit_location,
        visit_attendees=fu.visit_attendees,
        visit_purpose=fu.visit_purpose,
        follower_id=fu.follower_id,
        created_at=fu.created_at,
        terminal_customer_name=customer_name,
        follower_name=follower_name,
        lead_name=lead_name,
        opportunity_name=opportunity_name,
        project_name=project_name,
        channel_name=channel_name,
    )


@router.get("/", response_model=list[FollowUpRead])
async def list_follow_ups(
    terminal_customer_id: Optional[int] = None,
    lead_id: Optional[int] = None,
    opportunity_id: Optional[int] = None,
    project_id: Optional[int] = None,
    channel_id: Optional[int] = None,
    follow_up_type: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    principal = build_principal(current_user)

    query = (
        select(
            FollowUp,
            TerminalCustomer.customer_name,
            User.name,
            Lead.lead_name,
            Opportunity.opportunity_name,
            Project.project_name,
            Channel.company_name,
        )
        .outerjoin(
            TerminalCustomer, FollowUp.terminal_customer_id == TerminalCustomer.id
        )
        .outerjoin(User, FollowUp.follower_id == User.id)
        .outerjoin(Lead, FollowUp.lead_id == Lead.id)
        .outerjoin(Opportunity, FollowUp.opportunity_id == Opportunity.id)
        .outerjoin(Project, FollowUp.project_id == Project.id)
        .outerjoin(Channel, FollowUp.channel_id == Channel.id)
    )

    query = await policy_service.scope_query(
        resource="follow_up",
        action="list",
        principal=principal,
        db=db,
        query=query,
        model=FollowUp,
    )

    if terminal_customer_id:
        query = query.where(FollowUp.terminal_customer_id == terminal_customer_id)
    if lead_id:
        query = query.where(FollowUp.lead_id == lead_id)
    if opportunity_id:
        query = query.where(FollowUp.opportunity_id == opportunity_id)
    if project_id:
        query = query.where(FollowUp.project_id == project_id)
    if channel_id:
        query = query.where(FollowUp.channel_id == channel_id)
    if follow_up_type:
        query = query.where(FollowUp.follow_up_type == follow_up_type)
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
        channel_name = row[6] if len(row) > 6 else None
        follow_ups.append(
            _build_follow_up_read(
                fu,
                customer_name,
                follower_name,
                lead_name,
                opp_name,
                proj_name,
                channel_name,
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
    if (
        not follow_up.lead_id
        and not follow_up.opportunity_id
        and not follow_up.project_id
        and not follow_up.channel_id
    ):
        raise HTTPException(
            status_code=400,
            detail="关联线索、关联商机、关联项目、关联渠道至少需要选择一个",
        )

    # 推断跟进类型
    follow_up_type = _infer_follow_up_type(
        follow_up.lead_id,
        follow_up.opportunity_id,
        follow_up.project_id,
        follow_up.channel_id,
        follow_up.follow_up_type,
    )

    # 验证字段约束
    _validate_follow_up_fields(follow_up_type, follow_up.follow_up_conclusion)

    principal = build_principal(current_user)

    if follow_up.channel_id:
        channel_result = await db.execute(
            select(Channel).where(Channel.id == follow_up.channel_id)
        )
        channel = channel_result.scalar_one_or_none()
        if not channel:
            raise HTTPException(status_code=404, detail="Channel not found")
        await policy_service.authorize(
            resource="channel",
            action="update",
            principal=principal,
            db=db,
            obj=channel,
        )

    terminal_customer_id = await _resolve_terminal_customer_id(
        db,
        follow_up.lead_id,
        follow_up.opportunity_id,
        follow_up.project_id,
    )
    await policy_service.authorize_create(
        resource="follow_up",
        principal=principal,
        db=db,
        payload=type(
            "FollowUpAuthPayload",
            (),
            {
                "follower_id": current_user["id"],
                "lead_id": follow_up.lead_id,
                "opportunity_id": follow_up.opportunity_id,
                "project_id": follow_up.project_id,
                "terminal_customer_id": terminal_customer_id,
                "channel_id": follow_up.channel_id,
            },
        )(),
    )

    new_follow_up = FollowUp(
        terminal_customer_id=terminal_customer_id,
        lead_id=follow_up.lead_id,
        opportunity_id=follow_up.opportunity_id,
        project_id=follow_up.project_id,
        channel_id=follow_up.channel_id,
        follow_up_type=follow_up_type,
        follow_up_date=_parse_date(follow_up.follow_up_date),
        follow_up_method=follow_up.follow_up_method,
        follow_up_content=follow_up.follow_up_content,
        follow_up_conclusion=follow_up.follow_up_conclusion,
        next_action=follow_up.next_action,
        next_follow_up_date=_parse_date(follow_up.next_follow_up_date),
        follower_id=current_user["id"],
        created_at=date.today(),
        visit_location=follow_up.visit_location,
        visit_attendees=follow_up.visit_attendees,
        visit_purpose=follow_up.visit_purpose,
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
    if follow_up.channel_id:
        related_entity.append(f"渠道#{follow_up.channel_id}")

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
    channel_name = None

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
        result = await db.execute(
            select(Lead.lead_name).where(Lead.id == follow_up.lead_id)
        )
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
    if follow_up.channel_id:
        result = await db.execute(
            select(Channel.company_name).where(Channel.id == follow_up.channel_id)
        )
        row = result.first()
        if row:
            channel_name = row[0]

    return _build_follow_up_read(
        new_follow_up,
        customer_name,
        follower_name,
        lead_name,
        opp_name,
        proj_name,
        channel_name,
    )


@router.put("/{follow_up_id}", response_model=FollowUpRead)
async def update_follow_up(
    follow_up_id: int,
    follow_up: FollowUpUpdate,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    principal = build_principal(current_user)
    result = await db.execute(select(FollowUp).where(FollowUp.id == follow_up_id))
    existing = result.scalar_one_or_none()
    if not existing:
        raise HTTPException(status_code=404, detail="FollowUp not found")

    await policy_service.authorize(
        resource="follow_up",
        action="update",
        principal=principal,
        db=db,
        obj=existing,
    )

    update_data = follow_up.model_dump(exclude_unset=True)
    target_lead_id = update_data.get("lead_id", existing.lead_id)
    target_opportunity_id = update_data.get("opportunity_id", existing.opportunity_id)
    target_project_id = update_data.get("project_id", existing.project_id)
    target_channel_id = update_data.get("channel_id", existing.channel_id)

    # 处理跟进类型更新
    new_follow_up_type = _infer_follow_up_type(
        target_lead_id,
        target_opportunity_id,
        target_project_id,
        target_channel_id,
        update_data.get("follow_up_type", existing.follow_up_type),
    )

    # 验证字段约束
    new_conclusion = update_data.get(
        "follow_up_conclusion", existing.follow_up_conclusion
    )
    _validate_follow_up_fields(new_follow_up_type, new_conclusion)

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

    if target_channel_id:
        channel_result = await db.execute(
            select(Channel).where(Channel.id == target_channel_id)
        )
        channel = channel_result.scalar_one_or_none()
        if not channel:
            raise HTTPException(status_code=404, detail="Channel not found")
        await policy_service.authorize(
            resource="channel",
            action="update",
            principal=principal,
            db=db,
            obj=channel,
        )

    await policy_service.authorize_create(
        resource="follow_up",
        principal=principal,
        db=db,
        payload=type(
            "FollowUpAuthPayload",
            (),
            {
                "follower_id": existing.follower_id,
                "lead_id": target_lead_id,
                "opportunity_id": target_opportunity_id,
                "project_id": target_project_id,
                "terminal_customer_id": target_terminal_customer_id,
                "channel_id": target_channel_id,
            },
        )(),
    )

    for field, value in update_data.items():
        if field in ["follow_up_date", "next_follow_up_date"]:
            value = _parse_date(value)
        setattr(existing, field, value)

    # 确保跟进类型被正确设置
    existing.follow_up_type = new_follow_up_type

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
    channel_name = None

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
        result = await db.execute(
            select(User.name).where(User.id == existing.follower_id)
        )
        row = result.first()
        if row:
            follower_name = row[0]
    if existing.lead_id:
        result = await db.execute(
            select(Lead.lead_name).where(Lead.id == existing.lead_id)
        )
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
    if existing.channel_id:
        result = await db.execute(
            select(Channel.company_name).where(Channel.id == existing.channel_id)
        )
        row = result.first()
        if row:
            channel_name = row[0]

    return _build_follow_up_read(
        existing,
        customer_name,
        follower_name,
        lead_name,
        opp_name,
        proj_name,
        channel_name,
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

    principal = build_principal(current_user)
    await policy_service.authorize(
        resource="follow_up",
        action="delete",
        principal=principal,
        db=db,
        obj=follow_up,
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
