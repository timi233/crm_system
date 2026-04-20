from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import date


class NineABase(BaseModel):
    key_events: Optional[str] = None
    budget: Optional[float] = None
    decision_chain_influence: Optional[str] = None
    customer_challenges: Optional[str] = None
    customer_needs: Optional[str] = None
    solution_differentiation: Optional[str] = None
    competitors: Optional[str] = None
    buying_method: Optional[str] = None
    close_date: Optional[date] = None


class NineACreate(NineABase):
    pass


class NineAUpdate(NineABase):
    pass


class NineARead(NineABase):
    id: int
    opportunity_id: int

    model_config = ConfigDict(from_attributes=True)


class NineAVersionRead(NineABase):
    id: int
    opportunity_id: int
    version_number: int
    created_at: Optional[str] = None
    created_by_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
