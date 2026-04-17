from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class CustomerChannelLinkBase(BaseModel):
    customer_id: int
    channel_id: int
    role: str = Field(..., pattern="^(主渠道|协作渠道|历史渠道)$")
    discount_rate: Optional[float] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    notes: Optional[str] = None


class CustomerChannelLinkCreate(CustomerChannelLinkBase):
    pass


class CustomerChannelLinkRead(CustomerChannelLinkBase):
    id: int
    channel_name: Optional[str] = None
    channel_code: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class CustomerChannelLinkUpdate(BaseModel):
    role: Optional[str] = Field(None, pattern="^(主渠道|协作渠道|历史渠道)$")
    discount_rate: Optional[float] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    notes: Optional[str] = None
