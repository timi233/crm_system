from pydantic import BaseModel, ConfigDict
from typing import Optional


class CustomerBase(BaseModel):
    customer_name: str
    credit_code: str
    customer_industry: str
    customer_region: str
    customer_owner_id: int
    channel_id: Optional[int] = None
    main_contact: Optional[str] = None
    phone: Optional[str] = None
    customer_status: str = "Active"
    maintenance_expiry: Optional[str] = None
    notes: Optional[str] = None


class CustomerCreate(CustomerBase):
    pass


class CustomerRead(CustomerBase):
    id: int
    customer_code: str
    customer_owner_name: Optional[str] = None
    channel_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
