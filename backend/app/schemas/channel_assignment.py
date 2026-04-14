from pydantic import BaseModel, ConfigDict
from datetime import datetime

from app.models.channel_assignment import PermissionLevel


class ChannelAssignmentBase(BaseModel):
    user_id: int
    channel_id: int
    permission_level: PermissionLevel = PermissionLevel.read
    target_responsibility: bool = False


class ChannelAssignmentCreate(ChannelAssignmentBase):
    pass


class ChannelAssignmentRead(BaseModel):
    id: int
    user_id: int
    channel_id: int
    permission_level: PermissionLevel
    assigned_at: datetime | None = None
    assigned_by: int | None = None
    target_responsibility: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None
    user_name: str | None = None
    channel_name: str | None = None

    model_config = ConfigDict(from_attributes=True)


class ChannelAssignmentUpdate(BaseModel):
    permission_level: PermissionLevel | None = None
    target_responsibility: bool | None = None
