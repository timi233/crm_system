from typing import Any, Optional

from pydantic import BaseModel, ConfigDict


class SalesTargetCreate(BaseModel):
    user_id: int
    target_year: int
    target_amount: float


class SalesTargetUpdate(BaseModel):
    user_id: int
    target_year: int
    target_amount: float


class SalesTargetRead(BaseModel):
    id: int
    user_id: int
    target_type: str
    target_year: int
    target_period: int
    target_amount: float
    parent_id: Optional[int] = None
    created_at: Optional[Any] = None
    updated_at: Optional[Any] = None

    model_config = ConfigDict(from_attributes=True)


class QuarterDecomposeRequest(BaseModel):
    q1: float = 0
    q2: float = 0
    q3: float = 0
    q4: float = 0
