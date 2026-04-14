from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import List, Optional

from app.models.knowledge import KnowledgeSourceType


class KnowledgeBase(BaseModel):
    title: str
    problem_type: Optional[str] = None
    problem: str
    solution: str
    tags: Optional[List[str]] = None
    source_type: KnowledgeSourceType = KnowledgeSourceType.manual
    source_id: Optional[int] = None


class KnowledgeCreate(KnowledgeBase):
    model_config = ConfigDict(from_attributes=True)


class KnowledgeRead(BaseModel):
    id: int
    title: str
    problem_type: Optional[str] = None
    problem_type_name: Optional[str] = None
    problem: str
    solution: str
    tags: Optional[List[str]] = None
    source_type: KnowledgeSourceType
    source_type_name: Optional[str] = None
    source_id: Optional[int] = None
    view_count: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None
    created_by_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class KnowledgeUpdate(BaseModel):
    title: Optional[str] = None
    problem_type: Optional[str] = None
    problem: Optional[str] = None
    solution: Optional[str] = None
    tags: Optional[List[str]] = None
    source_type: Optional[KnowledgeSourceType] = None
    source_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class KnowledgeSearchRequest(BaseModel):
    keyword: Optional[str] = None
    problem_type: Optional[str] = None
    tags: Optional[List[str]] = None

    model_config = ConfigDict(from_attributes=True)
