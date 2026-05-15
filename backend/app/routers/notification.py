from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database import get_db
from app.schemas.notification import (
    MarkAllReadRequest,
    NotificationRead,
    NotificationListResponse,
    UnreadCountResponse,
)
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["notifications"])


def _to_read_schema(n) -> NotificationRead:
    return NotificationRead(
        id=n.id,
        notification_type=n.notification_type,
        title=n.title,
        content=n.content,
        entity_type=n.entity_type,
        entity_id=n.entity_id,
        entity_code=n.entity_code,
        is_read=n.is_read,
        created_at=n.created_at,
        read_at=n.read_at,
    )


@router.get("", response_model=NotificationListResponse)
async def list_notifications(
    is_read: Optional[bool] = Query(None),
    type: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    service = NotificationService(db)
    items = await service.list_user_notifications(
        current_user["id"],
        is_read=is_read,
        notification_type=type,
        skip=skip,
        limit=limit,
    )
    total = await service.count_user_notifications(
        current_user["id"],
        is_read=is_read,
        notification_type=type,
    )
    return NotificationListResponse(
        items=[_to_read_schema(n) for n in items],
        total=total,
    )


@router.get("/unread-count", response_model=UnreadCountResponse)
async def get_unread_count(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    service = NotificationService(db)
    count = await service.count_unread(current_user["id"])
    return UnreadCountResponse(count=count)


@router.post("/{notification_id}/mark-read", response_model=NotificationRead)
async def mark_notification_read(
    notification_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    service = NotificationService(db)
    notification = await service.mark_read(notification_id, current_user["id"])
    if not notification:
        raise HTTPException(status_code=404, detail="通知不存在或无权操作")
    return _to_read_schema(notification)


@router.post("/mark-all-read")
async def mark_all_read(
    body: MarkAllReadRequest = MarkAllReadRequest(),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    service = NotificationService(db)
    count = await service.mark_all_read(
        current_user["id"],
        notification_type=body.notification_type,
    )
    return {"success": True, "marked_count": count}
