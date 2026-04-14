from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

from app.models.execution_plan import PlanType, ExecutionPlanStatus


class ExecutionPlanBase(BaseModel):
    channel_id: int
    user_id: int
    plan_type: PlanType
    plan_period: str
    plan_content: str
    execution_status: Optional[str] = None
    key_obstacles: Optional[str] = None
    next_steps: Optional[str] = None
    status: ExecutionPlanStatus


class ExecutionPlanCreate(ExecutionPlanBase):
    pass


class ExecutionPlanRead(BaseModel):
    id: int
    channel_id: int
    user_id: int
    plan_type: PlanType
    plan_period: str
    plan_content: str
    execution_status: Optional[str] = None
    key_obstacles: Optional[str] = None
    next_steps: Optional[str] = None
    status: ExecutionPlanStatus
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    channel_name: Optional[str] = None
    user_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ExecutionPlanUpdate(BaseModel):
    channel_id: Optional[int] = None
    user_id: Optional[int] = None
    plan_type: Optional[PlanType] = None
    plan_period: Optional[str] = None
    plan_content: Optional[str] = None
    execution_status: Optional[str] = None
    key_obstacles: Optional[str] = None
    next_steps: Optional[str] = None
    status: Optional[ExecutionPlanStatus] = None
