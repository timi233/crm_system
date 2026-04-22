from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class PlanType(enum.Enum):
    monthly = "monthly"
    weekly = "weekly"


class PlanCategory(enum.Enum):
    general = "general"
    training = "training"


class ExecutionPlanStatus(enum.Enum):
    planned = "planned"
    in_progress = "in-progress"
    completed = "completed"
    archived = "archived"


class ExecutionPlan(Base):
    __tablename__ = "execution_plans"

    id = Column(Integer, primary_key=True, index=True)
    channel_id = Column(Integer, ForeignKey("channels.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    plan_type = Column(Enum(PlanType, native_enum=False), nullable=False, index=True)
    plan_category = Column(
        Enum(PlanCategory, native_enum=False),
        nullable=False,
        default=PlanCategory.general,
        server_default=PlanCategory.general.value,
        index=True,
    )
    plan_period = Column(String(20), nullable=False, index=True)
    plan_content = Column(Text, nullable=False)

    execution_status = Column(Text, nullable=True)
    key_obstacles = Column(Text, nullable=True)
    next_steps = Column(Text, nullable=True)
    status = Column(
        Enum(ExecutionPlanStatus, native_enum=False),
        default=ExecutionPlanStatus.planned,
        nullable=False,
        index=True,
    )

    created_at = Column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=True, index=True
    )
    updated_at = Column(TIMESTAMP(timezone=True), onupdate=func.now(), nullable=True)

    channel = relationship("Channel", back_populates="execution_plans")
    user = relationship("User", back_populates="execution_plans")
