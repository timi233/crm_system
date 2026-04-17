from pydantic import BaseModel, ConfigDict
from typing import Optional, List


class ProjectBase(BaseModel):
    project_name: str
    terminal_customer_id: int
    sales_owner_id: int
    business_type: str
    project_status: str
    downstream_contract_amount: float
    upstream_procurement_amount: Optional[float] = None
    direct_project_investment: Optional[float] = None
    additional_investment: Optional[float] = None
    winning_date: Optional[str] = None
    acceptance_date: Optional[str] = None
    first_payment_date: Optional[str] = None
    actual_payment_amount: Optional[float] = None
    notes: Optional[str] = None
    product_ids: Optional[List[int]] = None
    products: Optional[List[str]] = None
    channel_id: Optional[int] = None
    source_opportunity_id: Optional[int] = None


class ProjectCreate(ProjectBase):
    pass


class ProjectRead(ProjectBase):
    id: int
    project_code: str
    gross_margin: Optional[float] = None
    terminal_customer_name: Optional[str] = None
    sales_owner_name: Optional[str] = None
    products: Optional[List[str]] = None

    model_config = ConfigDict(from_attributes=True)


class ProjectUpdate(BaseModel):
    project_name: Optional[str] = None
    terminal_customer_id: Optional[int] = None
    sales_owner_id: Optional[int] = None
    business_type: Optional[str] = None
    project_status: Optional[str] = None
    downstream_contract_amount: Optional[float] = None
    upstream_procurement_amount: Optional[float] = None
    direct_project_investment: Optional[float] = None
    additional_investment: Optional[float] = None
    winning_date: Optional[str] = None
    acceptance_date: Optional[str] = None
    first_payment_date: Optional[str] = None
    actual_payment_amount: Optional[float] = None
    notes: Optional[str] = None
    product_ids: Optional[List[int]] = None
    products: Optional[List[str]] = None
    channel_id: Optional[int] = None
    source_opportunity_id: Optional[int] = None
    gross_margin: Optional[float] = None
