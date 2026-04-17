from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import date


class LeadBase(BaseModel):
    lead_name: str
    terminal_customer_id: int
    channel_id: Optional[int] = None
    source_channel_id: Optional[int] = None
    lead_stage: str = "初步接触"
    lead_source: Optional[str] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    products: Optional[List[str]] = None
    estimated_budget: Optional[float] = None
    has_confirmed_requirement: bool = False
    has_confirmed_budget: bool = False
    sales_owner_id: int
    notes: Optional[str] = None


class LeadCreate(LeadBase):
    pass


class LeadRead(BaseModel):
    id: int
    lead_code: str
    lead_name: str
    terminal_customer_id: int
    channel_id: Optional[int] = None
    channel_name: Optional[str] = None
    source_channel_id: Optional[int] = None
    source_channel_name: Optional[str] = None
    lead_stage: str
    lead_source: Optional[str] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    products: Optional[List[str]] = None
    estimated_budget: Optional[float] = None
    has_confirmed_requirement: bool = False
    has_confirmed_budget: bool = False
    converted_to_opportunity: bool = False
    opportunity_id: Optional[int] = None
    sales_owner_id: int
    notes: Optional[str] = None
    created_at: Optional[date] = None
    updated_at: Optional[date] = None
    terminal_customer_name: Optional[str] = None
    sales_owner_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class LeadUpdate(BaseModel):
    lead_name: Optional[str] = None
    terminal_customer_id: Optional[int] = None
    channel_id: Optional[int] = None
    lead_stage: Optional[str] = None
    lead_source: Optional[str] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    products: Optional[List[str]] = None
    estimated_budget: Optional[float] = None
    has_confirmed_requirement: Optional[bool] = None
    has_confirmed_budget: Optional[bool] = None
    sales_owner_id: Optional[int] = None
    notes: Optional[str] = None


class LeadConvertRequest(BaseModel):
    opportunity_name: str
    expected_contract_amount: float
    opportunity_source: Optional[str] = None
    lead_grade: Optional[str] = None
