from typing import Optional

from pydantic import BaseModel, ConfigDict


class DictItemCreate(BaseModel):
    dict_type: str
    code: str
    name: str
    parent_id: Optional[int] = None
    sort_order: int = 0
    is_active: bool = True
    extra_data: Optional[dict] = None


class DictItemRead(BaseModel):
    id: int
    dict_type: str
    code: str
    name: str
    parent_id: Optional[int] = None
    sort_order: int = 0
    is_active: bool
    extra_data: Optional[dict] = None

    model_config = ConfigDict(from_attributes=True)


class DictItemUpdate(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    parent_id: Optional[int] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None
    extra_data: Optional[dict] = None
