from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime, date
from decimal import Decimal
from app.models.unified_target import TargetType


class UnifiedTargetBase(BaseModel):
    target_type: TargetType
    channel_id: Optional[int] = None
    user_id: Optional[int] = None
    year: int
    quarter: Optional[int] = None
    month: Optional[int] = None
    performance_target: Optional[Decimal] = None
    opportunity_target: Optional[Decimal] = None
    project_count_target: Optional[int] = None
    development_goal: Optional[str] = None


class UnifiedTargetCreate(UnifiedTargetBase):
    pass


class UnifiedTargetRead(UnifiedTargetBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None
    channel_name: Optional[str] = None
    user_name: Optional[str] = None
    achieved_performance: Optional[Decimal] = None
    achieved_opportunity: Optional[Decimal] = None
    achieved_project_count: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class UnifiedTargetUpdate(BaseModel):
    target_type: Optional[TargetType] = None
    channel_id: Optional[int] = None
    user_id: Optional[int] = None
    year: Optional[int] = None
    quarter: Optional[int] = None
    month: Optional[int] = None
    performance_target: Optional[Decimal] = None
    opportunity_target: Optional[Decimal] = None
    project_count_target: Optional[int] = None
    development_goal: Optional[str] = None
