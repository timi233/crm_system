"""
Finance-specific view schemas for CRM system.

These schemas are used for the /customers/{id}/finance-view endpoint,
which provides financial data only (contracts, payment plans, project financials)
to finance role users, excluding sensitive business data like follow_up_content.
"""

from pydantic import BaseModel
from typing import List, Optional
from decimal import Decimal
from datetime import date


class PaymentPlanView(BaseModel):
    """Payment plan data for finance view."""

    id: int
    contract_code: str
    contract_name: str
    plan_stage: str
    plan_amount: Decimal
    plan_date: Optional[date]
    actual_amount: Optional[Decimal]
    actual_date: Optional[date]
    payment_status: str

    class Config:
        from_attributes = True


class ProjectFinanceView(BaseModel):
    """Project financial data for finance view (excludes sensitive business fields)."""

    id: int
    project_code: str
    project_name: str
    project_status: str
    downstream_contract_amount: Decimal
    upstream_procurement_amount: Optional[Decimal]
    direct_project_investment: Optional[Decimal]
    additional_investment: Optional[Decimal]
    gross_margin: Optional[Decimal]
    actual_payment_amount: Optional[Decimal]
    winning_date: Optional[date]
    acceptance_date: Optional[date]
    first_payment_date: Optional[date]

    class Config:
        from_attributes = True


class ContractFinanceView(BaseModel):
    """Contract data for finance view."""

    id: int
    contract_code: str
    contract_name: str
    contract_direction: str
    contract_status: str
    contract_amount: Decimal
    signing_date: Optional[date]
    effective_date: Optional[date]
    expiry_date: Optional[date]

    class Config:
        from_attributes = True


class CustomerFinanceView(BaseModel):
    """
    Customer finance-specific view.

    Only includes financial data: contracts, payment plans, project financials.
    Excludes sensitive business data: leads, opportunities, follow-ups, sales_owner names.
    """

    customer_id: int
    customer_name: str
    customer_code: str
    credit_code: str
    customer_status: str

    # Contract summary
    contracts: List[ContractFinanceView] = []
    total_contract_amount: Decimal = Decimal("0")
    downstream_contract_amount: Decimal = Decimal("0")
    upstream_contract_amount: Decimal = Decimal("0")
    signed_contract_count: int = 0
    pending_contract_count: int = 0

    # Payment plan summary
    payment_plans: List[PaymentPlanView] = []
    total_planned_amount: Decimal = Decimal("0")
    total_actual_amount: Decimal = Decimal("0")
    payment_completion_rate: float = 0.0

    # Project financial summary
    projects: List[ProjectFinanceView] = []
    total_project_downstream: Decimal = Decimal("0")
    total_project_upstream: Optional[Decimal] = None
    total_gross_margin: Optional[Decimal] = None

    class Config:
        from_attributes = True
