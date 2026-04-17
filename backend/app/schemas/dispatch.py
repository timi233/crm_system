from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, computed_field


class TechnicianInfo(BaseModel):
    id: int
    name: str
    phone: Optional[str]
    department: Optional[str]


class DispatchRecordBase(BaseModel):
    work_order_id: str
    work_order_no: Optional[str]
    source_type: str
    status: str = "pending"
    order_type: Optional[str]
    customer_name: Optional[str]
    priority: Optional[str]
    description: Optional[str]


class DispatchRecordRead(DispatchRecordBase):
    id: int
    lead_id: Optional[int]
    opportunity_id: Optional[int]
    project_id: Optional[int]
    previous_status: Optional[str]
    status_updated_at: Optional[datetime]
    created_at: datetime
    dispatched_at: Optional[datetime]
    completed_at: Optional[datetime]
    technician_ids: Optional[List[str]] = None
    technician_names: Optional[List[str]] = None
    estimated_start_date: Optional[date] = None
    estimated_start_period: Optional[str] = None
    estimated_end_date: Optional[date] = None
    estimated_end_period: Optional[str] = None

    @computed_field
    @property
    def source_id(self) -> Optional[int]:
        if self.source_type == "lead" and self.lead_id:
            return self.lead_id
        if self.source_type == "opportunity" and self.opportunity_id:
            return self.opportunity_id
        if self.source_type == "project" and self.project_id:
            return self.project_id
        return None

    model_config = ConfigDict(from_attributes=True)


class DispatchWebhookPayload(BaseModel):
    event: str
    work_order_id: str
    work_order_no: Optional[str]
    status: str
    previous_status: Optional[str]
    timestamp: str
    metadata: Optional[dict] = None


class DispatchApplicationRequest(BaseModel):
    technician_ids: List[int]
    service_mode: str = "offline"
    start_date: Optional[str] = None
    start_period: Optional[str] = None
    end_date: Optional[str] = None
    end_period: Optional[str] = None
    work_type: Optional[str] = None
    notes: Optional[str] = None


class DispatchApplicationResponse(BaseModel):
    success: bool
    message: str
    work_order_id: Optional[str] = None
    work_order_no: Optional[str] = None
