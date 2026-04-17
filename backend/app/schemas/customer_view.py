from pydantic import BaseModel
from typing import Optional, List


class CustomerFullView(BaseModel):
    customer: dict
    channel: Optional[dict] = None
    summary: dict
    leads: List[dict]
    opportunities: List[dict]
    projects: List[dict]
    follow_ups: List[dict]
    contracts: List[dict]
