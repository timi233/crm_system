from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class DashboardSummaryResponse(BaseModel):
    leads_count: int
    opportunities_count: int
    projects_count: int
    contracts_count: int
    pending_followups: int
    alerts_count: int
    won_opportunities: int
    lost_opportunities: int
    quarterly_target: float
    quarterly_achieved: float
    monthly_target: float
    monthly_achieved: float
    quarterly_forecast_amount: float
    monthly_target_prev: Optional[float] = None
    monthly_achieved_prev: Optional[float] = None
    quarterly_target_prev: Optional[float] = None
    quarterly_achieved_prev: Optional[float] = None
    leads_count_prev: Optional[int] = None
    opportunities_count_prev: Optional[int] = None


class DashboardTodoItem(BaseModel):
    id: int
    type: str
    title: str
    customer_name: str
    due_date: Optional[str]
    priority: str
    entity_type: str
    entity_id: int


class DashboardFollowUpItem(BaseModel):
    id: int
    customer_name: str
    follow_up_date: str
    follow_up_method: str
    follow_up_content: str
    follower_name: str
    entity_type: str
    entity_id: int


class DashboardNotificationItem(BaseModel):
    id: int
    type: str
    title: str
    content: str
    created_at: str
    is_read: bool
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    entity_code: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class TeamRankItem(BaseModel):
    rank: int
    user_id: int
    user_name: str
    amount: float


class MarkNotificationsReadRequest(BaseModel):
    notifications: List[dict]
