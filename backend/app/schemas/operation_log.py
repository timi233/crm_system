from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class OperationLogRead(BaseModel):
    id: int
    user_id: int
    user_name: str
    action_type: str
    entity_type: str
    entity_id: int
    entity_code: Optional[str] = None
    entity_name: Optional[str] = None
    old_value: Optional[dict] = None
    new_value: Optional[dict] = None
    description: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
