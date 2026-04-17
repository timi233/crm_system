from typing import List

from pydantic import BaseModel


class SalesFunnelResponse(BaseModel):
    leads: dict
    opportunities: dict
    projects: dict
    contracts: dict
    conversion_rates: dict


class PerformanceByUser(BaseModel):
    user_id: int
    user_name: str
    contract_count: int
    contract_amount: float
    received_amount: float
    pending_amount: float
    gross_margin: float


class PerformanceReportResponse(BaseModel):
    by_user: List[PerformanceByUser]
    by_month: List[dict]
    total_contract_amount: float
    total_received_amount: float
    total_pending_amount: float


class PaymentProgressResponse(BaseModel):
    total_plan_amount: float
    total_actual_amount: float
    total_pending_amount: float
    overdue_amount: float
    overdue_count: int
    contracts: List[dict]
    progress_percentage: float
