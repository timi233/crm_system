from pydantic import BaseModel, ConfigDict
from datetime import datetime, date
from typing import Optional, List
from app.models.work_order import (
    OrderType,
    WorkOrderPriority,
    WorkOrderStatus,
    SourceType,
)


class WorkOrderBase(BaseModel):
    order_type: OrderType = OrderType.CF
    submitter_id: int
    related_sales_id: Optional[int] = None
    customer_name: str
    customer_contact: Optional[str] = None
    customer_phone: Optional[str] = None
    has_channel: bool = False
    channel_id: Optional[int] = None
    channel_name: Optional[str] = None
    channel_contact: Optional[str] = None
    channel_phone: Optional[str] = None
    manufacturer_contact: Optional[str] = None
    work_type: Optional[str] = None
    priority: WorkOrderPriority = WorkOrderPriority.NORMAL
    description: str
    estimated_start_date: Optional[date] = None
    estimated_start_period: Optional[str] = None
    estimated_end_date: Optional[date] = None
    estimated_end_period: Optional[str] = None
    service_summary: Optional[str] = None
    cancel_reason: Optional[str] = None
    source_type: Optional[SourceType] = None
    lead_id: Optional[int] = None
    opportunity_id: Optional[int] = None
    project_id: Optional[int] = None


class WorkOrderCreate(WorkOrderBase):
    pass


class WorkOrderRead(BaseModel):
    id: int
    cuid_id: Optional[str] = None
    work_order_no: str
    order_type: OrderType
    submitter_id: int
    related_sales_id: Optional[int] = None
    customer_name: str
    customer_contact: Optional[str] = None
    customer_phone: Optional[str] = None
    has_channel: bool
    channel_id: Optional[int] = None
    channel_name: Optional[str] = None
    channel_contact: Optional[str] = None
    channel_phone: Optional[str] = None
    manufacturer_contact: Optional[str] = None
    work_type: Optional[str] = None
    priority: WorkOrderPriority
    description: str
    status: WorkOrderStatus
    estimated_start_date: Optional[date] = None
    estimated_start_period: Optional[str] = None
    estimated_end_date: Optional[date] = None
    estimated_end_period: Optional[str] = None
    accepted_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    service_summary: Optional[str] = None
    cancel_reason: Optional[str] = None
    source_type: Optional[SourceType] = None
    lead_id: Optional[int] = None
    opportunity_id: Optional[int] = None
    project_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    submitter_name: Optional[str] = None
    related_sales_name: Optional[str] = None
    channel_name_display: Optional[str] = None
    technician_names: List[str] = []

    model_config = ConfigDict(from_attributes=True)


class WorkOrderUpdate(BaseModel):
    work_order_no: Optional[str] = None
    order_type: Optional[OrderType] = None
    related_sales_id: Optional[int] = None
    customer_name: Optional[str] = None
    customer_contact: Optional[str] = None
    customer_phone: Optional[str] = None
    has_channel: Optional[bool] = None
    channel_id: Optional[int] = None
    channel_name: Optional[str] = None
    channel_contact: Optional[str] = None
    channel_phone: Optional[str] = None
    manufacturer_contact: Optional[str] = None
    work_type: Optional[str] = None
    priority: Optional[WorkOrderPriority] = None
    description: Optional[str] = None
    estimated_start_date: Optional[date] = None
    estimated_start_period: Optional[str] = None
    estimated_end_date: Optional[date] = None
    estimated_end_period: Optional[str] = None
    service_summary: Optional[str] = None
    cancel_reason: Optional[str] = None
    source_type: Optional[SourceType] = None
    lead_id: Optional[int] = None
    opportunity_id: Optional[int] = None
    project_id: Optional[int] = None


class WorkOrderStatusUpdate(BaseModel):
    status: WorkOrderStatus
    service_summary: Optional[str] = None
    cancel_reason: Optional[str] = None


class WorkOrderAssignRequest(BaseModel):
    technician_ids: List[int]


class WorkOrderListResponse(BaseModel):
    total: int
    items: List[WorkOrderRead]
