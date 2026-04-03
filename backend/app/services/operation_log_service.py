"""
Operation Log Service for recording user actions.
"""

from datetime import datetime
from typing import Optional, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.operation_log import (
    OperationLog,
    ACTION_CREATE,
    ACTION_UPDATE,
    ACTION_DELETE,
    ACTION_CONVERT,
    ACTION_STAGE_CHANGE,
)


async def log_operation(
    db: AsyncSession,
    user_id: int,
    user_name: str,
    action_type: str,
    entity_type: str,
    entity_id: int,
    entity_code: Optional[str] = None,
    entity_name: Optional[str] = None,
    old_value: Optional[dict] = None,
    new_value: Optional[dict] = None,
    description: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> OperationLog:
    """
    Record an operation log entry.
    """
    log = OperationLog(
        user_id=user_id,
        user_name=user_name,
        action_type=action_type,
        entity_type=entity_type,
        entity_id=entity_id,
        entity_code=entity_code,
        entity_name=entity_name,
        old_value=old_value,
        new_value=new_value,
        description=description,
        ip_address=ip_address,
        created_at=datetime.utcnow(),
    )
    db.add(log)
    await db.flush()
    return log


async def log_create(
    db: AsyncSession,
    user_id: int,
    user_name: str,
    entity_type: str,
    entity_id: int,
    entity_code: Optional[str] = None,
    entity_name: Optional[str] = None,
    new_value: Optional[dict] = None,
    description: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> OperationLog:
    return await log_operation(
        db=db,
        user_id=user_id,
        user_name=user_name,
        action_type=ACTION_CREATE,
        entity_type=entity_type,
        entity_id=entity_id,
        entity_code=entity_code,
        entity_name=entity_name,
        new_value=new_value,
        description=description or f"创建{entity_type}: {entity_name or entity_code}",
        ip_address=ip_address,
    )


async def log_update(
    db: AsyncSession,
    user_id: int,
    user_name: str,
    entity_type: str,
    entity_id: int,
    entity_code: Optional[str] = None,
    entity_name: Optional[str] = None,
    old_value: Optional[dict] = None,
    new_value: Optional[dict] = None,
    description: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> OperationLog:
    return await log_operation(
        db=db,
        user_id=user_id,
        user_name=user_name,
        action_type=ACTION_UPDATE,
        entity_type=entity_type,
        entity_id=entity_id,
        entity_code=entity_code,
        entity_name=entity_name,
        old_value=old_value,
        new_value=new_value,
        description=description or f"更新{entity_type}: {entity_name or entity_code}",
        ip_address=ip_address,
    )


async def log_delete(
    db: AsyncSession,
    user_id: int,
    user_name: str,
    entity_type: str,
    entity_id: int,
    entity_code: Optional[str] = None,
    entity_name: Optional[str] = None,
    old_value: Optional[dict] = None,
    description: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> OperationLog:
    return await log_operation(
        db=db,
        user_id=user_id,
        user_name=user_name,
        action_type=ACTION_DELETE,
        entity_type=entity_type,
        entity_id=entity_id,
        entity_code=entity_code,
        entity_name=entity_name,
        old_value=old_value,
        description=description or f"删除{entity_type}: {entity_name or entity_code}",
        ip_address=ip_address,
    )


async def log_convert(
    db: AsyncSession,
    user_id: int,
    user_name: str,
    source_type: str,
    source_id: int,
    target_type: str,
    target_id: int,
    source_code: Optional[str] = None,
    source_name: Optional[str] = None,
    target_code: Optional[str] = None,
    description: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> OperationLog:
    return await log_operation(
        db=db,
        user_id=user_id,
        user_name=user_name,
        action_type=ACTION_CONVERT,
        entity_type=source_type,
        entity_id=source_id,
        entity_code=source_code,
        entity_name=source_name,
        new_value={
            "target_type": target_type,
            "target_id": target_id,
            "target_code": target_code,
        },
        description=description
        or f"转换{source_type}为{target_type}: {source_name or source_code}",
        ip_address=ip_address,
    )


async def log_stage_change(
    db: AsyncSession,
    user_id: int,
    user_name: str,
    entity_type: str,
    entity_id: int,
    old_stage: str,
    new_stage: str,
    entity_code: Optional[str] = None,
    entity_name: Optional[str] = None,
    description: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> OperationLog:
    return await log_operation(
        db=db,
        user_id=user_id,
        user_name=user_name,
        action_type=ACTION_STAGE_CHANGE,
        entity_type=entity_type,
        entity_id=entity_id,
        entity_code=entity_code,
        entity_name=entity_name,
        old_value={"stage": old_stage},
        new_value={"stage": new_stage},
        description=description or f"{entity_type}阶段变更: {old_stage} → {new_stage}",
        ip_address=ip_address,
    )


async def get_logs_by_entity(
    db: AsyncSession,
    entity_type: str,
    entity_id: int,
    limit: int = 50,
) -> list[OperationLog]:
    result = await db.execute(
        select(OperationLog)
        .where(OperationLog.entity_type == entity_type)
        .where(OperationLog.entity_id == entity_id)
        .order_by(OperationLog.created_at.desc())
        .limit(limit)
    )
    return result.scalars().all()


async def get_logs_by_user(
    db: AsyncSession,
    user_id: int,
    limit: int = 50,
) -> list[OperationLog]:
    result = await db.execute(
        select(OperationLog)
        .where(OperationLog.user_id == user_id)
        .order_by(OperationLog.created_at.desc())
        .limit(limit)
    )
    return result.scalars().all()
