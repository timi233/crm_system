from datetime import date, datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database import get_db
from app.models.operation_log import OperationLog
from app.schemas.operation_log import OperationLogRead
from app.services.operation_log_service import get_logs_by_entity, get_logs_by_user


router = APIRouter(prefix="/operation-logs", tags=["operation_logs"])


@router.get("/", response_model=List[OperationLogRead])
async def list_operation_logs(
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None,
    user_id: Optional[int] = None,
    action_type: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = 100,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(OperationLog).order_by(OperationLog.created_at.desc())

    if entity_type:
        query = query.where(OperationLog.entity_type == entity_type)
    if entity_id:
        query = query.where(OperationLog.entity_id == entity_id)
    if user_id:
        query = query.where(OperationLog.user_id == user_id)
    if action_type:
        query = query.where(OperationLog.action_type == action_type)
    if start_date:
        query = query.where(OperationLog.created_at >= start_date)
    if end_date:
        end_datetime = datetime.combine(end_date, datetime.max.time())
        query = query.where(OperationLog.created_at <= end_datetime)

    query = query.limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{log_id}", response_model=OperationLogRead)
async def get_operation_log(
    log_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(OperationLog).where(OperationLog.id == log_id))
    log = result.scalar_one_or_none()
    if not log:
        raise HTTPException(status_code=404, detail="Operation log not found")
    return log


@router.get("/entity/{entity_type}/{entity_id}", response_model=List[OperationLogRead])
async def get_entity_logs(
    entity_type: str,
    entity_id: int,
    limit: int = 50,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_logs_by_entity(db, entity_type, entity_id, limit)


@router.get("/user/{user_id}", response_model=List[OperationLogRead])
async def get_user_logs(
    user_id: int,
    limit: int = 50,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_logs_by_user(db, user_id, limit)
