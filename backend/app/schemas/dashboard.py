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


class DashboardMetricCard(BaseModel):
    key: str
    title: str
    value: float
    unit: str = ""
    trend: Optional[float] = None
    status: str = "normal"
    link: Optional[str] = None


class DashboardTodoItemNew(BaseModel):
    key: str
    title: str
    description: Optional[str] = None
    priority: str = "normal"
    due_date: Optional[str] = None
    link: Optional[str] = None


class DashboardRiskItem(BaseModel):
    key: str
    title: str
    description: Optional[str] = None
    severity: str = "low"
    link: Optional[str] = None


class DashboardQuickAction(BaseModel):
    key: str
    title: str
    link: str
    capability: Optional[str] = None


class DashboardReportStatus(BaseModel):
    daily: Optional[str] = None
    weekly: Optional[str] = None
    daily_draft_id: Optional[int] = None
    weekly_draft_id: Optional[int] = None


class DashboardWorkbenchResponse(BaseModel):
    role: str
    scope: str
    metrics: List[DashboardMetricCard] = []
    todos: List[DashboardTodoItemNew] = []
    risks: List[DashboardRiskItem] = []
    quick_actions: List[DashboardQuickAction] = []
    report_status: Optional[DashboardReportStatus] = None
    generated_at: str
