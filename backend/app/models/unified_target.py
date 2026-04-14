from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    TIMESTAMP,
    ForeignKey,
    DECIMAL,
    Boolean,
    Enum,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class TargetType(enum.Enum):
    channel = "channel"
    person = "person"


class UnifiedTarget(Base):
    __tablename__ = "unified_targets"

    id = Column(Integer, primary_key=True, index=True)

    target_type = Column(
        Enum(TargetType, native_enum=False), nullable=False, index=True
    )
    channel_id = Column(Integer, ForeignKey("channels.id"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)

    year = Column(Integer, nullable=False, index=True)
    quarter = Column(Integer, nullable=True, index=True)
    month = Column(Integer, nullable=True, index=True)

    performance_target = Column(DECIMAL(10, 2), nullable=True)
    opportunity_target = Column(DECIMAL(10, 2), nullable=True)
    project_count_target = Column(Integer, nullable=True)
    development_goal = Column(Text, nullable=True)

    achieved_performance = Column(DECIMAL(10, 2), default=0, nullable=True)
    achieved_opportunity = Column(DECIMAL(10, 2), default=0, nullable=True)
    achieved_project_count = Column(Integer, default=0, nullable=True)

    created_at = Column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=True, index=True
    )
    updated_at = Column(TIMESTAMP(timezone=True), onupdate=func.now(), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    channel = relationship("Channel", back_populates="channel_targets")
    user = relationship("User", foreign_keys=[user_id])
    creator = relationship("User", foreign_keys=[created_by])
