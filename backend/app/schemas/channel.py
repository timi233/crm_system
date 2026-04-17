from pydantic import BaseModel, ConfigDict
from typing import Optional
from decimal import Decimal
from datetime import datetime


class ChannelBase(BaseModel):
    company_name: str
    channel_type: str
    status: str = "合作中"
    main_contact: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    province: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    credit_code: Optional[str] = None
    bank_name: Optional[str] = None
    bank_account: Optional[str] = None
    website: Optional[str] = None
    wechat: Optional[str] = None
    cooperation_products: Optional[str] = None
    cooperation_region: Optional[str] = None
    discount_rate: Optional[Decimal] = None
    billing_info: Optional[str] = None
    notes: Optional[str] = None


class ChannelCreate(ChannelBase):
    pass


class ChannelUpdate(BaseModel):
    company_name: Optional[str] = None
    channel_type: Optional[str] = None
    status: Optional[str] = None
    main_contact: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    province: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    credit_code: Optional[str] = None
    bank_name: Optional[str] = None
    bank_account: Optional[str] = None
    website: Optional[str] = None
    wechat: Optional[str] = None
    cooperation_products: Optional[str] = None
    cooperation_region: Optional[str] = None
    discount_rate: Optional[Decimal] = None
    billing_info: Optional[str] = None
    notes: Optional[str] = None


class ChannelRead(ChannelBase):
    id: int
    channel_code: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ChannelFullView(BaseModel):
    channel: dict
    summary: dict
    customers: list[dict]
    opportunities: list[dict]
    projects: list[dict]
    contracts: list[dict]
    work_orders: list[dict]
    assignments: list[dict]
    execution_plans: list[dict]
    targets: list[dict]
