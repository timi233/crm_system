from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional

from app.database import get_db
from app.core.dependencies import get_current_user
from app.core.channel_permissions import (
    apply_channel_scope_filter,
    require_channel_permission,
    require_channel_create,
    require_channel_delete,
    check_channel_exists,
)
from app.models.channel import Channel
from app.models.work_order import WorkOrder
from app.models.channel_assignment import ChannelAssignment
from app.models.execution_plan import ExecutionPlan
from app.models.unified_target import UnifiedTarget, TargetType
from app.models.user import User
from app.schemas.channel import ChannelCreate, ChannelRead, ChannelUpdate
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
    await db.commit()
    await db.refresh(new_channel)

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
    return new_channel


@router.get("/{channel_id}", response_model=ChannelRead)
async def get_channel(
    channel_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _: None = Depends(require_channel_permission("read")),
):
    channel = await check_channel_exists(db, channel_id)
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
    existing = await check_channel_exists(db, channel_id)

    for field, value in channel.model_dump(exclude_unset=True).items():
        setattr(existing, field, value)
    existing.last_modified_by = current_user.get("id")

    await db.commit()
    await db.refresh(existing)

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
    return existing


@router.delete("/{channel_id}")
async def delete_channel(
    channel_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _: None = Depends(require_channel_delete()),
):
    channel = await check_channel_exists(db, channel_id)

    company_name = channel.company_name
    await db.delete(channel)
    await db.commit()

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
    return {"message": "Channel deleted successfully"}


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
        assignment_dict = assignment.__dict__.copy()
        assignment_dict["user_name"] = user_name
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


@router.post("/{channel_id}/refresh-performance")
async def refresh_channel_performance_endpoint(
    channel_id: int,
    current_user: dict = Depends(require_channel_permission("write")),
    db: AsyncSession = Depends(get_db),
):
    await refresh_channel_performance(db, channel_id)
    return {"message": "Channel performance refreshed"}
