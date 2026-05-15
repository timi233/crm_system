import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        user_id: int,
        notification_type: str,
        title: str,
        content: str,
        entity_type: Optional[str] = None,
        entity_id: Optional[int] = None,
        entity_code: Optional[str] = None,
    ) -> Notification:
        notification = Notification(
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            content=content,
            entity_type=entity_type,
            entity_id=entity_id,
            entity_code=entity_code,
            created_at=datetime.utcnow(),
        )
        self.db.add(notification)
        try:
            await self.db.commit()
            await self.db.refresh(notification)
        except Exception:
            await self.db.rollback()
            logger.error(f"Failed to create notification for user {user_id}: {notification_type}")
            raise
        return notification

    async def list_user_notifications(
        self,
        user_id: int,
        *,
        is_read: Optional[bool] = None,
        notification_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> List[Notification]:
        limit = min(max(limit, 1), 100)
        query = select(Notification).where(Notification.user_id == user_id)
        if is_read is not None:
            query = query.where(Notification.is_read == is_read)
        if notification_type:
            query = query.where(Notification.notification_type == notification_type)
        query = query.order_by(Notification.created_at.desc()).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def count_unread(self, user_id: int) -> int:
        result = await self.db.execute(
            select(func.count()).where(
                Notification.user_id == user_id,
                Notification.is_read == False,
            )
        )
        return result.scalar() or 0

    async def count_user_notifications(
        self,
        user_id: int,
        *,
        is_read: Optional[bool] = None,
        notification_type: Optional[str] = None,
    ) -> int:
        query = select(func.count()).where(Notification.user_id == user_id)
        if is_read is not None:
            query = query.where(Notification.is_read == is_read)
        if notification_type:
            query = query.where(Notification.notification_type == notification_type)
        result = await self.db.execute(query)
        return result.scalar() or 0

    async def mark_read(self, notification_id: int, user_id: int) -> Optional[Notification]:
        result = await self.db.execute(
            select(Notification).where(
                Notification.id == notification_id,
                Notification.user_id == user_id,
            )
        )
        notification = result.scalar_one_or_none()
        if not notification:
            return None
        if not notification.is_read:
            notification.is_read = True
            notification.read_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(notification)
        return notification

    async def mark_all_read(
        self,
        user_id: int,
        notification_type: Optional[str] = None,
    ) -> int:
        query = (
            select(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.is_read == False,
            )
        )
        if notification_type:
            query = query.where(Notification.notification_type == notification_type)
        result = await self.db.execute(query)
        notifications = result.scalars().all()
        now = datetime.utcnow()
        for n in notifications:
            n.is_read = True
            n.read_at = now
        await self.db.commit()
        return len(notifications)
