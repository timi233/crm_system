from typing import Optional

from pydantic import BaseModel, ConfigDict


class ProductBase(BaseModel):
    product_name: str
    product_type: str
    brand_manufacturer: str
    is_active: bool = True
    notes: Optional[str] = None


class ProductCreate(ProductBase):
    pass


class ProductRead(ProductBase):
    id: int
    product_code: str

    model_config = ConfigDict(from_attributes=True)


class ProductUpdate(BaseModel):
    product_name: Optional[str] = None
    product_type: Optional[str] = None
    brand_manufacturer: Optional[str] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None
