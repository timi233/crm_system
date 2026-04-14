from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional


class EvaluationBase(BaseModel):
    work_order_id: int
    quality_rating: int
    response_rating: int
    customer_feedback: Optional[str] = None
    improvement_suggestion: Optional[str] = None
    recommend: bool = False


class EvaluationCreate(EvaluationBase):
    pass


class EvaluationRead(BaseModel):
    id: int
    work_order_id: int
    quality_rating: int
    response_rating: int
    customer_feedback: Optional[str] = None
    improvement_suggestion: Optional[str] = None
    recommend: bool
    evaluator_id: int
    created_at: Optional[datetime] = None
    work_order_no: Optional[str] = None
    work_order_info: Optional[dict] = None

    model_config = ConfigDict(from_attributes=True)


class EvaluationUpdate(BaseModel):
    quality_rating: Optional[int] = None
    response_rating: Optional[int] = None
    customer_feedback: Optional[str] = None
    improvement_suggestion: Optional[str] = None
    recommend: Optional[bool] = None

    model_config = ConfigDict(from_attributes=True)
