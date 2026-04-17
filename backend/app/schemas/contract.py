from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import date


class ContractProductCreate(BaseModel):
    product_id: int
    product_name: str
    quantity: float = 1
    unit_price: float = 0
    discount: float = 1.0
    amount: float = 0
    notes: Optional[str] = None


class ContractProductRead(ContractProductCreate):
    id: int
    contract_id: int

    model_config = ConfigDict(from_attributes=True)


class PaymentPlanCreate(BaseModel):
    plan_stage: str
    plan_amount: float
    plan_date: Optional[str] = None
    actual_amount: Optional[float] = 0
    actual_date: Optional[str] = None
    payment_status: str = "pending"
    notes: Optional[str] = None


class PaymentPlanRead(PaymentPlanCreate):
    id: int
    contract_id: int
    plan_date: Optional[date] = None
    actual_date: Optional[date] = None

    model_config = ConfigDict(from_attributes=True)


class ContractBase(BaseModel):
    contract_name: str
    project_id: int
    contract_direction: str = "Downstream"
    contract_status: str = "draft"
    terminal_customer_id: Optional[int] = None
    channel_id: Optional[int] = None
    contract_amount: float = 0
    signing_date: Optional[str] = None
    effective_date: Optional[str] = None
    expiry_date: Optional[str] = None
    contract_file_url: Optional[str] = None
    notes: Optional[str] = None


class ContractCreate(ContractBase):
    products: Optional[List[ContractProductCreate]] = []
    payment_plans: Optional[List[PaymentPlanCreate]] = []


class ContractRead(ContractBase):
    id: int
    contract_code: str
    signing_date: Optional[date] = None
    effective_date: Optional[date] = None
    expiry_date: Optional[date] = None
    created_at: Optional[date] = None
    updated_at: Optional[date] = None
    products: List[ContractProductRead] = []
    payment_plans: List[PaymentPlanRead] = []
    project_name: Optional[str] = None
    terminal_customer_name: Optional[str] = None
    channel_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ContractUpdate(BaseModel):
    contract_name: Optional[str] = None
    contract_status: Optional[str] = None
    terminal_customer_id: Optional[int] = None
    channel_id: Optional[int] = None
    contract_amount: Optional[float] = None
    signing_date: Optional[str] = None
    effective_date: Optional[str] = None
    expiry_date: Optional[str] = None
    contract_file_url: Optional[str] = None
    notes: Optional[str] = None
    products: Optional[List[ContractProductCreate]] = None
    payment_plans: Optional[List[PaymentPlanCreate]] = None
