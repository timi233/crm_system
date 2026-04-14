from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List

from app.database import get_db
from app.core.dependencies import get_current_user
from app.models.channel_assignment import ChannelAssignment
from app.models.user import User
from app.models.channel import Channel
from app.schemas.channel_assignment import (
    ChannelAssignmentCreate,
    ChannelAssignmentRead,
    ChannelAssignmentUpdate,
)
from app.services.operation_log_service import (
    log_create,
    log_update,
    log_delete,
)

router = APIRouter(prefix="/channel-assignments", tags=["channel-assignments"])


@router.get("/", response_model=List[ChannelAssignmentRead])
async def list_channel_assignments(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await db.execute(
        select(ChannelAssignment).options(
            selectinload(ChannelAssignment.user),
            selectinload(ChannelAssignment.channel),
        )
    )
    assignments = result.scalars().all()

    response = []
    for assignment in assignments:
        response.append(ChannelAssignmentRead.model_validate(assignment))

    return response


@router.post("/", response_model=ChannelAssignmentRead)
async def create_channel_assignment(
    assignment: ChannelAssignmentCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    user_result = await db.execute(select(User).where(User.id == assignment.user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=400, detail=f"User with id {assignment.user_id} not found"
        )

    channel_result = await db.execute(
        select(Channel).where(Channel.id == assignment.channel_id)
    )
    channel = channel_result.scalar_one_or_none()
    if not channel:
        raise HTTPException(
            status_code=400, detail=f"Channel with id {assignment.channel_id} not found"
        )

    new_assignment = ChannelAssignment(
        user_id=assignment.user_id,
        channel_id=assignment.channel_id,
        permission_level=assignment.permission_level,
        target_responsibility=assignment.target_responsibility,
        assigned_by=current_user.get("id") if current_user else None,
    )
    db.add(new_assignment)
    await db.commit()
    await db.refresh(new_assignment)

    await log_create(
        db=db,
        user_id=current_user.get("id", 0) if current_user else 0,
        user_name=current_user.get("name", "") if current_user else "",
        entity_type="channel_assignment",
        entity_id=new_assignment.id,
        entity_name=f"{user.name} - {channel.company_name}",
        description=f"分配渠道权限: {user.name} 对 {channel.company_name} 的权限为 {assignment.permission_level.value}",
        ip_address=request.client.host if request.client else None,
    )

    response = ChannelAssignmentRead.model_validate(new_assignment)
    response.user_name = user.name
    response.channel_name = channel.company_name
    return response


@router.get("/{assignment_id}", response_model=ChannelAssignmentRead)
async def get_channel_assignment(
    assignment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await db.execute(
        select(ChannelAssignment)
        .options(
            selectinload(ChannelAssignment.user),
            selectinload(ChannelAssignment.channel),
        )
        .where(ChannelAssignment.id == assignment_id)
    )
    assignment = result.scalar_one_or_none()

    if not assignment:
        raise HTTPException(status_code=404, detail="Channel assignment not found")

    response = ChannelAssignmentRead.model_validate(assignment)
    if assignment.user:
        response.user_name = assignment.user.name
    if assignment.channel:
        response.channel_name = assignment.channel.company_name
    return response


@router.put("/{assignment_id}", response_model=ChannelAssignmentRead)
async def update_channel_assignment(
    assignment_id: int,
    assignment: ChannelAssignmentUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await db.execute(
        select(ChannelAssignment).where(ChannelAssignment.id == assignment_id)
    )
    existing = result.scalar_one_or_none()

    if not existing:
        raise HTTPException(status_code=404, detail="Channel assignment not found")

    if assignment.user_id is not None and assignment.user_id != existing.user_id:
        user_result = await db.execute(
            select(User).where(User.id == assignment.user_id)
        )
        user = user_result.scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=400, detail=f"User with id {assignment.user_id} not found"
            )

    if (
        assignment.channel_id is not None
        and assignment.channel_id != existing.channel_id
    ):
        channel_result = await db.execute(
            select(Channel).where(Channel.id == assignment.channel_id)
        )
        channel = channel_result.scalar_one_or_none()
        if not channel:
            raise HTTPException(
                status_code=400,
                detail=f"Channel with id {assignment.channel_id} not found",
            )

    if assignment.permission_level is not None:
        existing.permission_level = assignment.permission_level
    if assignment.target_responsibility is not None:
        existing.target_responsibility = assignment.target_responsibility
    if assignment.user_id is not None:
        existing.user_id = assignment.user_id
    if assignment.channel_id is not None:
        existing.channel_id = assignment.channel_id

    await db.commit()
    await db.refresh(existing)

    user_name = existing.user.name if existing.user else ""
    channel_name = existing.channel.company_name if existing.channel else ""

    await log_update(
        db=db,
        user_id=current_user.get("id", 0) if current_user else 0,
        user_name=current_user.get("name", "") if current_user else "",
        entity_type="channel_assignment",
        entity_id=existing.id,
        entity_name=f"{user_name} - {channel_name}",
        description=f"更新渠道权限: {user_name} 对 {channel_name} 的权限被修改",
        ip_address=request.client.host if request.client else None,
    )

    response = ChannelAssignmentRead.model_validate(existing)
    response.user_name = user_name
    response.channel_name = channel_name
    return response


@router.delete("/{assignment_id}")
async def delete_channel_assignment(
    assignment_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await db.execute(
        select(ChannelAssignment).where(ChannelAssignment.id == assignment_id)
    )
    assignment = result.scalar_one_or_none()

    if not assignment:
        raise HTTPException(status_code=404, detail="Channel assignment not found")

    user_name = assignment.user.name if assignment.user else ""
    channel_name = assignment.channel.company_name if assignment.channel else ""

    await db.delete(assignment)
    await db.commit()

    await log_delete(
        db=db,
        user_id=current_user.get("id", 0) if current_user else 0,
        user_name=current_user.get("name", "") if current_user else "",
        entity_type="channel_assignment",
        entity_id=assignment_id,
        entity_name=f"{user_name} - {channel_name}",
        description=f"删除渠道权限: {user_name} 对 {channel_name} 的权限",
        ip_address=request.client.host if request.client else None,
    )

    return {"message": "Channel assignment deleted successfully"}
