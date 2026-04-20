from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ChannelContactBase(BaseModel):
    name: str
    title: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    is_primary: bool = False
    notes: Optional[str] = None


class ChannelContactCreate(ChannelContactBase):
    pass


class ChannelContactUpdate(BaseModel):
    name: Optional[str] = None
    title: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    is_primary: Optional[bool] = None
    notes: Optional[str] = None


class ChannelContactRead(ChannelContactBase):
    id: int
    channel_id: int
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
