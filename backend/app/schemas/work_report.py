from datetime import date
from typing import Any, Optional
from pydantic import BaseModel, ConfigDict, Field


class WorkReportCreate(BaseModel):
    report_type: str = Field(..., pattern="^(daily|weekly)$")
    report_date: date
    week_start: Optional[date] = None
    week_end: Optional[date] = None
    remark: Optional[str] = None


class WorkReportUpdate(BaseModel):
    remark: Optional[str] = None


class WorkReportRead(BaseModel):
    id: int
    report_type: str
    report_date: date
    week_start: Optional[date] = None
    week_end: Optional[date] = None
    owner_id: int
    owner_role: Optional[str] = None
    status: str
    structured_snapshot: Optional[dict[str, Any]] = None
    remark: Optional[str] = None
    source_report_ids: Optional[list[int]] = None
    submitted_at: Optional[Any] = None
    withdrawn_at: Optional[Any] = None
    created_at: Optional[Any] = None
    updated_at: Optional[Any] = None

    model_config = ConfigDict(from_attributes=True)


class WorkReportGenerateDraftRequest(BaseModel):
    report_type: str = Field(..., pattern="^(daily|weekly)$")
    report_date: date


class WorkReportListQuery(BaseModel):
    report_type: Optional[str] = Field(None, pattern="^(daily|weekly)$")
    owner_id: Optional[int] = Field(None, gt=0)
    status: Optional[str] = Field(None, pattern="^(draft|submitted|withdrawn)$")
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    skip: int = Field(0, ge=0)
    limit: int = Field(20, ge=1, le=100)


class WorkReportCommentCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=1000)


class WorkReportCommentRead(BaseModel):
    id: int
    report_id: int
    user_id: int
    content: str
    created_at: Optional[Any] = None

    model_config = ConfigDict(from_attributes=True)
