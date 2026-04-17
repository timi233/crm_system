from typing import Optional

from pydantic import BaseModel, ConfigDict


class AlertItem(BaseModel):
    alert_type: str
    priority: str
    title: str
    content: str
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    entity_code: Optional[str] = None
    entity_name: Optional[str] = None
    created_at: str


class AlertSummary(BaseModel):
    high: int
    medium: int
    low: int
    total: int


class AlertRuleCreate(BaseModel):
    rule_code: str
    rule_name: str
    rule_type: str
    entity_type: str
    priority: str = "medium"
    threshold_days: int = 0
    threshold_amount: int = 0
    description: Optional[str] = None
    is_active: bool = True


class AlertRuleUpdate(BaseModel):
    rule_code: str
    rule_name: str
    rule_type: str
    entity_type: str
    priority: str = "medium"
    threshold_days: int = 0
    threshold_amount: int = 0
    description: Optional[str] = None
    is_active: bool = True


class AlertRuleRead(AlertRuleCreate):
    id: int
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
