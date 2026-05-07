from typing import Any, Optional

from pydantic import BaseModel, ConfigDict


class SalesTargetCreate(BaseModel):
    user_id: int
    target_year: int
    target_amount: float
    gross_profit_target: float = 0.0


class SalesTargetUpdate(BaseModel):
    target_amount: Optional[float] = None
    gross_profit_target: Optional[float] = None


class SalesTargetRead(BaseModel):
    id: int
    user_id: int
    target_type: str
    target_year: int
    target_period: int
    target_amount: float
    gross_profit_target: float = 0.0
    parent_id: Optional[int] = None
    remaining_rev: float = 0.0
    remaining_gp: float = 0.0
    created_at: Optional[Any] = None
    updated_at: Optional[Any] = None

    model_config = ConfigDict(from_attributes=True)


class QuarterlyDecomposeRequest(BaseModel):
    """Partially decompose yearly into quarters and months"""
    quarters: dict[int, float] = {}
    quarters_gp: dict[int, float] = {}
    months_by_quarter: dict[int, dict[int, float]] = {}
    months_gp_by_quarter: dict[int, dict[int, float]] = {}


class ActualPerformanceCreate(BaseModel):
    target_id: Optional[int] = None
    year: int
    month: int
    amount_actual: float = 0.0
    gross_profit_actual: float = 0.0


class ActualPerformanceUpdate(BaseModel):
    target_id: Optional[int] = None
    amount_actual: Optional[float] = None
    gross_profit_actual: Optional[float] = None


class ActualPerformanceRead(BaseModel):
    id: int
    user_id: int
    target_id: Optional[int] = None
    year: int
    month: int
    amount_actual: float
    gross_profit_actual: float
    created_at: Optional[Any] = None
    updated_at: Optional[Any] = None

    model_config = ConfigDict(from_attributes=True)
