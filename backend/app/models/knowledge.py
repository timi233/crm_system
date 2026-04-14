from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, Enum, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class KnowledgeSourceType(enum.Enum):
    manual = "manual"
    work_order = "work_order"


class Knowledge(Base):
    __tablename__ = "knowledge"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    problem_type = Column(String(100), nullable=True, index=True)
    problem = Column(Text, nullable=False)
    solution = Column(Text, nullable=False)
    tags = Column(ARRAY(String), nullable=True)

    source_type = Column(
        Enum(KnowledgeSourceType, native_enum=False),
        default=KnowledgeSourceType.manual,
        nullable=False,
    )
    source_id = Column(Integer, nullable=True)

    view_count = Column(Integer, default=0, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=True, index=True
    )
    updated_at = Column(TIMESTAMP(timezone=True), onupdate=func.now(), nullable=True)

    # Relationship to user
    creator = relationship("User", foreign_keys=[created_by])
