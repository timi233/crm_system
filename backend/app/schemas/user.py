from pydantic import BaseModel, Field
from pydantic.config import ConfigDict
from typing import Optional


class UserCreate(BaseModel):
    name: str
    email: str
    password: str
    role: str = Field(..., pattern="^(admin|sales|business|finance|technician|tech|channel_ops)$")
    functional_role: Optional[str] = Field(None, pattern="^(TECHNICIAN|SALES)$")
    sales_leader_id: Optional[int] = None
    department_manager_id: Optional[int] = None
    sales_region: Optional[str] = None
    sales_product_line: Optional[str] = None


class UserRead(BaseModel):
    id: int
    name: str
    email: str
    role: str
    functional_role: Optional[str] = None
    sales_leader_id: Optional[int] = None
    department_manager_id: Optional[int] = None
    sales_region: Optional[str] = None
    sales_product_line: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = Field(
        None, pattern="^(admin|sales|business|finance|technician|tech|channel_ops)$"
    )
    functional_role: Optional[str] = Field(None, pattern="^(TECHNICIAN|SALES)$")
    sales_leader_id: Optional[int] = None
    department_manager_id: Optional[int] = None
    sales_region: Optional[str] = None
    sales_product_line: Optional[str] = None
    is_active: Optional[bool] = None
