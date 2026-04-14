from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import List, Optional
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from datetime import datetime

from app.database import get_db
from app.models.unified_target import UnifiedTarget, TargetType
from app.models.user import User
from app.models.channel import Channel
from app.core.dependencies import get_current_user
from app.schemas.unified_target import (
    UnifiedTargetCreate,
    UnifiedTargetRead,
    UnifiedTargetUpdate,
)
from app.services.operation_log_service import (
    log_create,
    log_update,
    log_delete,
)

router = APIRouter(prefix="/unified-targets", tags=["unified-targets"])


@router.get("/", response_model=List[UnifiedTargetRead])
async def list_unified_targets(
    year: Optional[int] = None,
    quarter: Optional[int] = None,
    month: Optional[int] = None,
    channel_id: Optional[int] = None,
    user_id: Optional[int] = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(UnifiedTarget).options(
        selectinload(UnifiedTarget.channel),
        selectinload(UnifiedTarget.user),
    )

    if year:
        stmt = stmt.where(UnifiedTarget.year == year)
    if quarter is not None:
        stmt = stmt.where(UnifiedTarget.quarter == quarter)
    if month is not None:
        stmt = stmt.where(UnifiedTarget.month == month)
    if channel_id:
        stmt = stmt.where(UnifiedTarget.channel_id == channel_id)
    if user_id:
        stmt = stmt.where(UnifiedTarget.user_id == user_id)

    result = await db.execute(stmt)
    targets = result.scalars().all()

    return [
        {
            **target.__dict__,
            "channel_name": target.channel.company_name if target.channel else None,
            "user_name": target.user.name if target.user else None,
            "achieved_performance": (
                float(target.achieved_performance)
                if target.achieved_performance
                else None
            ),
            "achieved_opportunity": (
                float(target.achieved_opportunity)
                if target.achieved_opportunity
                else None
            ),
            "achieved_project_count": target.achieved_project_count,
        }
        for target in targets
    ]


@router.post("/", response_model=UnifiedTargetRead)
async def create_unified_target(
    target: UnifiedTargetCreate,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Validate: either channel_id or user_id must be provided
    if target.channel_id is None and target.user_id is None:
        raise HTTPException(
            status_code=400,
            detail="Either channel_id or user_id must be provided (not both null)",
        )

    # Validate: channel exists if channel_id provided
    if target.channel_id is not None:
        channel_result = await db.execute(
            select(Channel).where(Channel.id == target.channel_id)
        )
        if not channel_result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Channel not found")

    # Validate: user exists if user_id provided
    if target.user_id is not None:
        user_result = await db.execute(select(User).where(User.id == target.user_id))
        if not user_result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="User not found")

    new_target = UnifiedTarget(
        target_type=target.target_type,
        channel_id=target.channel_id,
        user_id=target.user_id,
        year=target.year,
        quarter=target.quarter,
        month=target.month,
        performance_target=target.performance_target,
        opportunity_target=target.opportunity_target,
        project_count_target=target.project_count_target,
        development_goal=target.development_goal,
        created_at=datetime.now(),
        created_by=current_user["id"],
    )
    db.add(new_target)
    await db.flush()
    await db.refresh(new_target)

    await log_create(
        db=db,
        user_id=current_user["id"],
        user_name=current_user["name"],
        entity_type="unified_target",
        entity_id=new_target.id,
        entity_code=f"TARGET-{new_target.id}",
        entity_name=f"{target.target_type.value} target {new_target.year}",
        description=f"创建统一目标: {target.target_type.value} {new_target.year}",
        ip_address=request.client.host if request.client else None,
    )

    await db.commit()
    await db.refresh(new_target)

    return {
        **new_target.__dict__,
        "channel_name": new_target.channel.company_name if new_target.channel else None,
        "user_name": new_target.user.name if new_target.user else None,
        "achieved_performance": (
            float(new_target.achieved_performance)
            if new_target.achieved_performance
            else None
        ),
        "achieved_opportunity": (
            float(new_target.achieved_opportunity)
            if new_target.achieved_opportunity
            else None
        ),
        "achieved_project_count": new_target.achieved_project_count,
    }


@router.get("/{target_id}", response_model=UnifiedTargetRead)
async def get_unified_target(
    target_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(UnifiedTarget)
        .where(UnifiedTarget.id == target_id)
        .options(
            selectinload(UnifiedTarget.channel),
            selectinload(UnifiedTarget.user),
        )
    )
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="Unified target not found")

    return {
        **target.__dict__,
        "channel_name": target.channel.company_name if target.channel else None,
        "user_name": target.user.name if target.user else None,
        "achieved_performance": (
            float(target.achieved_performance) if target.achieved_performance else None
        ),
        "achieved_opportunity": (
            float(target.achieved_opportunity) if target.achieved_opportunity else None
        ),
        "achieved_project_count": target.achieved_project_count,
    }


@router.put("/{target_id}", response_model=UnifiedTargetRead)
async def update_unified_target(
    target_id: int,
    target: UnifiedTargetUpdate,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(UnifiedTarget).where(UnifiedTarget.id == target_id)
    )
    existing = result.scalar_one_or_none()
    if not existing:
        raise HTTPException(status_code=404, detail="Unified target not found")

    # Validate: channel exists if channel_id provided
    if target.channel_id is not None:
        channel_result = await db.execute(
            select(Channel).where(Channel.id == target.channel_id)
        )
        if not channel_result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Channel not found")

    # Validate: user exists if user_id provided
    if target.user_id is not None:
        user_result = await db.execute(select(User).where(User.id == target.user_id))
        if not user_result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="User not found")

    update_data = target.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(existing, field, value)

    await db.flush()

    await log_update(
        db=db,
        user_id=current_user["id"],
        user_name=current_user["name"],
        entity_type="unified_target",
        entity_id=existing.id,
        entity_code=f"TARGET-{existing.id}",
        entity_name=f"{existing.target_type.value} target {existing.year}",
        description=f"更新统一目标: {existing.target_type.value} {existing.year}",
        ip_address=request.client.host if request.client else None,
    )

    await db.commit()
    await db.refresh(existing)

    return {
        **existing.__dict__,
        "channel_name": existing.channel.company_name if existing.channel else None,
        "user_name": existing.user.name if existing.user else None,
        "achieved_performance": (
            float(existing.achieved_performance)
            if existing.achieved_performance
            else None
        ),
        "achieved_opportunity": (
            float(existing.achieved_opportunity)
            if existing.achieved_opportunity
            else None
        ),
        "achieved_project_count": existing.achieved_project_count,
    }


@router.delete("/{target_id}")
async def delete_unified_target(
    target_id: int,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(UnifiedTarget).where(UnifiedTarget.id == target_id)
    )
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="Unified target not found")

    await log_delete(
        db=db,
        user_id=current_user["id"],
        user_name=current_user["name"],
        entity_type="unified_target",
        entity_id=target.id,
        entity_code=f"TARGET-{target.id}",
        entity_name=f"{target.target_type.value} target {target.year}",
        description=f"删除统一目标: {target.target_type.value} {target.year}",
        ip_address=request.client.host if request.client else None,
    )

    await db.commit()
    return {"message": "Unified target deleted successfully"}


@router.post("/{target_id}/calculate")
async def calculate_target_achievement(
    target_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(UnifiedTarget).where(UnifiedTarget.id == target_id)
    )
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="Unified target not found")

    # TODO: Implement achievement calculation from related projects/opportunities
    # For now, return a stub response
    return {
        "target_id": target_id,
        "message": "Achievement calculation not yet implemented",
    }
