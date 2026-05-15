from datetime import date
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class TodoRead(BaseModel):
    key: str
    type: str
    title: str
    description: Optional[str] = None
    priority: str = "normal"
    due_date: Optional[str] = None
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    link: Optional[str] = None
    source: str = "system"
    status: str = "open"

    model_config = ConfigDict(from_attributes=True)


class TodoListResponse(BaseModel):
    items: List[TodoRead]
    total: int


class TodoFilterParams(BaseModel):
    type: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    skip: int = 0
    limit: int = 50