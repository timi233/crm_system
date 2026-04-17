from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import date, datetime


class ProductInstallationBase(BaseModel):
    manufacturer: str
    product_type: str
    product_model: Optional[str] = None
    license_scale: Optional[str] = None
    system_version: Optional[str] = None
    online_date: Optional[date] = None
    maintenance_expiry: Optional[date] = None
    username: Optional[str] = None
    password: Optional[str] = None
    login_url: Optional[str] = None
    notes: Optional[str] = None


class ProductInstallationCreate(ProductInstallationBase):
    customer_id: int


class ProductInstallationUpdate(BaseModel):
    manufacturer: Optional[str] = None
    product_type: Optional[str] = None
    product_model: Optional[str] = None
    license_scale: Optional[str] = None
    system_version: Optional[str] = None
    online_date: Optional[date] = None
    maintenance_expiry: Optional[date] = None
    username: Optional[str] = None
    password: Optional[str] = None
    login_url: Optional[str] = None
    notes: Optional[str] = None


class ProductInstallationRead(ProductInstallationBase):
    id: int
    customer_id: int
    customer_name: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by_id: Optional[int] = None
    created_by_name: Optional[str] = None

    can_view_credentials: bool = False

    model_config = ConfigDict(from_attributes=True)


class ProductInstallationWithCredentials(ProductInstallationRead):
    username_actual: Optional[str] = None
    password_actual: Optional[str] = None
    login_url_actual: Optional[str] = None
