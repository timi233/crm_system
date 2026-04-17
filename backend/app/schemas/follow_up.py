from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict


class FollowUpBase(BaseModel):
    lead_id: Optional[int] = None
    opportunity_id: Optional[int] = None
    project_id: Optional[int] = None
    follow_up_date: date
    follow_up_method: str
    follow_up_content: str
    follow_up_conclusion: str
    next_action: Optional[str] = None
    next_follow_up_date: Optional[date] = None


class FollowUpCreate(BaseModel):
    lead_id: Optional[int] = None
    opportunity_id: Optional[int] = None
    project_id: Optional[int] = None
    follow_up_date: str
    follow_up_method: str
    follow_up_content: str
    follow_up_conclusion: str
    next_action: Optional[str] = None
    next_follow_up_date: Optional[str] = None


class FollowUpRead(FollowUpBase):
    id: int
    terminal_customer_id: Optional[int] = None
    follower_id: int
    created_at: Optional[date] = None
    terminal_customer_name: Optional[str] = None
    lead_name: Optional[str] = None
    opportunity_name: Optional[str] = None
    project_name: Optional[str] = None
    follower_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class FollowUpUpdate(BaseModel):
    lead_id: Optional[int] = None
    opportunity_id: Optional[int] = None
    project_id: Optional[int] = None
    follow_up_date: Optional[str] = None
    follow_up_method: Optional[str] = None
    follow_up_content: Optional[str] = None
    follow_up_conclusion: Optional[str] = None
    next_action: Optional[str] = None
    next_follow_up_date: Optional[str] = None
