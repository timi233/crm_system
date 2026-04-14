from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date

from app.database import get_db
from app.core.dependencies import get_current_user, require_admin
from app.models.execution_plan import ExecutionPlan, PlanType, ExecutionPlanStatus
from app.models.user import User
from app.models.channel import Channel
from app.schemas.execution_plan import (
    ExecutionPlanCreate,
    ExecutionPlanRead,
    ExecutionPlanUpdate,
)

router = APIRouter(prefix="/execution-plans", tags=["execution-plans"])

EXECUTION_PLAN_STATUS_TRANSITIONS = {
    ExecutionPlanStatus.planned: [
        ExecutionPlanStatus.in_progress,
        ExecutionPlanStatus.archived,
    ],
    ExecutionPlanStatus.in_progress: [ExecutionPlanStatus.completed],
    ExecutionPlanStatus.completed: [ExecutionPlanStatus.archived],
    ExecutionPlanStatus.archived: [],
}


@router.get("/", response_model=List[ExecutionPlanRead])
async def list_execution_plans(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    channel_id: Optional[int] = None,
    user_id: Optional[int] = None,
    status: Optional[str] = None,
    plan_type: Optional[str] = None,
    plan_period: Optional[str] = None,
):
    stmt = select(ExecutionPlan).options(
        selectinload(ExecutionPlan.channel), selectinload(ExecutionPlan.user)
    )

    if channel_id:
        stmt = stmt.where(ExecutionPlan.channel_id == channel_id)
    if user_id:
        stmt = stmt.where(ExecutionPlan.user_id == user_id)
    if status:
        stmt = stmt.where(ExecutionPlan.status == ExecutionPlanStatus(status))
    if plan_type:
        stmt = stmt.where(ExecutionPlan.plan_type == PlanType(plan_type))
    if plan_period:
        stmt = stmt.where(ExecutionPlan.plan_period == plan_period)

    result = await db.execute(stmt)
    plans = result.scalars().all()
    return plans


@router.post("/", response_model=ExecutionPlanRead)
async def create_execution_plan(
    plan: ExecutionPlanCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    channel_result = await db.execute(
        select(Channel).where(Channel.id == plan.channel_id)
    )
    channel = channel_result.scalar_one_or_none()
    if not channel:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Channel with id {plan.channel_id} not found",
        )

    user_result = await db.execute(select(User).where(User.id == plan.user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User with id {plan.user_id} not found",
        )

    new_plan = ExecutionPlan(
        channel_id=plan.channel_id,
        user_id=plan.user_id,
        plan_type=plan.plan_type,
        plan_period=plan.plan_period,
        plan_content=plan.plan_content,
        execution_status=plan.execution_status,
        key_obstacles=plan.key_obstacles,
        next_steps=plan.next_steps,
        status=plan.status,
        created_at=date.today(),
        updated_at=date.today(),
    )
    db.add(new_plan)
    await db.flush()
    await db.commit()
    await db.refresh(new_plan)
    return new_plan


@router.get("/{plan_id}", response_model=ExecutionPlanRead)
async def get_execution_plan(
    plan_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(ExecutionPlan)
        .options(selectinload(ExecutionPlan.channel), selectinload(ExecutionPlan.user))
        .where(ExecutionPlan.id == plan_id)
    )
    result = await db.execute(stmt)
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Execution plan not found"
        )
    return plan


@router.put("/{plan_id}", response_model=ExecutionPlanRead)
async def update_execution_plan(
    plan_id: int,
    plan: ExecutionPlanUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    result = await db.execute(select(ExecutionPlan).where(ExecutionPlan.id == plan_id))
    existing = result.scalar_one_or_none()
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Execution plan not found"
        )

    update_data = plan.model_dump(exclude_unset=True)

    if "channel_id" in update_data and update_data["channel_id"] != existing.channel_id:
        channel_result = await db.execute(
            select(Channel).where(Channel.id == update_data["channel_id"])
        )
        channel = channel_result.scalar_one_or_none()
        if not channel:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Channel with id {update_data['channel_id']} not found",
            )

    if "user_id" in update_data and update_data["user_id"] != existing.user_id:
        user_result = await db.execute(
            select(User).where(User.id == update_data["user_id"])
        )
        user = user_result.scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User with id {update_data['user_id']} not found",
            )

    for field, value in update_data.items():
        setattr(existing, field, value)

    existing.updated_at = date.today()
    await db.flush()
    await db.commit()
    await db.refresh(existing)
    return existing


@router.delete("/{plan_id}")
async def delete_execution_plan(
    plan_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    result = await db.execute(select(ExecutionPlan).where(ExecutionPlan.id == plan_id))
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Execution plan not found"
        )
    await db.delete(plan)
    await db.commit()
    return {"message": "Execution plan deleted successfully"}


@router.patch("/{plan_id}/status")
async def update_execution_plan_status(
    plan_id: int,
    status_update: dict,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    result = await db.execute(select(ExecutionPlan).where(ExecutionPlan.id == plan_id))
    existing = result.scalar_one_or_none()
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Execution plan not found"
        )

    new_status_value = status_update.get("status")
    if not new_status_value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="-status field is required",
        )

    try:
        new_status = ExecutionPlanStatus(new_status_value)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status: {new_status_value}",
        )

    valid_transitions = EXECUTION_PLAN_STATUS_TRANSITIONS.get(existing.status, [])
    if new_status not in valid_transitions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Status cannot transition from '{existing.status.value}' to '{new_status.value}'",
        )

    existing.status = new_status
    existing.updated_at = date.today()
    await db.flush()
    await db.commit()
    await db.refresh(existing)
    return existing
