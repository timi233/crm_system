from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import date


class OpportunityBase(BaseModel):
    opportunity_name: str
    terminal_customer_id: int
    opportunity_source: str
    opportunity_stage: str
    expected_contract_amount: float
    expected_close_date: Optional[str] = None
    sales_owner_id: int
    channel_id: Optional[int] = None
    vendor_registration_status: Optional[str] = None
    vendor_discount: Optional[float] = None
    loss_reason: Optional[str] = None
    product_ids: Optional[List[int]] = None
    products: Optional[List[str]] = None


class OpportunityCreate(OpportunityBase):
    pass


class OpportunityRead(OpportunityBase):
    id: int
    opportunity_code: str
    project_id: Optional[int] = None
    created_at: Optional[date] = None
    terminal_customer_name: Optional[str] = None
    sales_owner_name: Optional[str] = None
    channel_name: Optional[str] = None
    products: Optional[List[str]] = None

    model_config = ConfigDict(from_attributes=True)


class OpportunityUpdate(BaseModel):
    opportunity_name: Optional[str] = None
    terminal_customer_id: Optional[int] = None
    opportunity_source: Optional[str] = None
    opportunity_stage: Optional[str] = None
    expected_contract_amount: Optional[float] = None
    expected_close_date: Optional[str] = None
    sales_owner_id: Optional[int] = None
    channel_id: Optional[int] = None
    vendor_registration_status: Optional[str] = None
    vendor_discount: Optional[float] = None
    loss_reason: Optional[str] = None
    product_ids: Optional[List[int]] = None
    products: Optional[List[str]] = None
    project_id: Optional[int] = None
