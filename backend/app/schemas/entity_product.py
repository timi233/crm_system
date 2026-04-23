from typing import Optional
from pydantic import BaseModel, ConfigDict
from datetime import date


class EntityProductBase(BaseModel):
    entity_type: str  # lead, opportunity, project
    entity_id: int
    product_type_id: int
    brand_id: Optional[int] = None
    model_id: Optional[int] = None
    quantity: Optional[int] = None
    unit_price: Optional[float] = None


class EntityProductCreate(EntityProductBase):
    pass


class EntityProductUpdate(BaseModel):
    product_type_id: Optional[int] = None
    brand_id: Optional[int] = None
    model_id: Optional[int] = None
    quantity: Optional[int] = None
    unit_price: Optional[float] = None


class EntityProductRead(EntityProductBase):
    id: int
    created_at: date
    
    model_config = ConfigDict(from_attributes=True)
