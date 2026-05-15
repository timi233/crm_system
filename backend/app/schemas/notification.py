from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class NotificationRead(BaseModel):
    id: int
    notification_type: str
    title: str
    content: str
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    entity_code: Optional[str] = None
    is_read: bool = False
    created_at: datetime
    read_at: Optional[datetime] = None


class NotificationListResponse(BaseModel):
    items: list[NotificationRead]
    total: int


class UnreadCountResponse(BaseModel):
    count: int


class MarkAllReadRequest(BaseModel):
    notification_type: Optional[str] = None
