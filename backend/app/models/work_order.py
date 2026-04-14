from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    TIMESTAMP,
    ForeignKey,
    Boolean,
    Date,
    Enum,
    Index,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class OrderType(enum.Enum):
    CF = "CF"
    CO = "CO"
    MF = "MF"
    MO = "MO"


class WorkOrderPriority(enum.Enum):
    NORMAL = "NORMAL"
    URGENT = "URGENT"
    VERY_URGENT = "VERY_URGENT"


class WorkOrderStatus(enum.Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    IN_SERVICE = "IN_SERVICE"
    DONE = "DONE"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


class SourceType(enum.Enum):
    lead = "lead"
    opportunity = "opportunity"
    project = "project"


class WorkOrder(Base):
    __tablename__ = "work_orders"

    id = Column(Integer, primary_key=True, index=True)
    cuid_id = Column(String(50), unique=True, nullable=True, index=True)
    work_order_no = Column(String(50), unique=True, nullable=False, index=True)
    order_type = Column(
        Enum(OrderType, native_enum=False),
        default=OrderType.CF,
        nullable=False,
        index=True,
    )

    submitter_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    related_sales_id = Column(
        Integer, ForeignKey("users.id"), nullable=True, index=True
    )

    customer_name = Column(String(255), nullable=False)
    customer_contact = Column(String(100), nullable=True)
    customer_phone = Column(String(50), nullable=True)

    has_channel = Column(Boolean, default=False, nullable=False)
    channel_id = Column(Integer, ForeignKey("channels.id"), nullable=True, index=True)
    channel_name = Column(String(100), nullable=True)
    channel_contact = Column(String(100), nullable=True)
    channel_phone = Column(String(50), nullable=True)

    manufacturer_contact = Column(String(100), nullable=True)

    work_type = Column(String(50), nullable=True)
    priority = Column(
        Enum(WorkOrderPriority, native_enum=False),
        default=WorkOrderPriority.NORMAL,
        nullable=False,
    )
    description = Column(Text, nullable=False)
    status = Column(
        Enum(WorkOrderStatus, native_enum=False),
        default=WorkOrderStatus.PENDING,
        nullable=False,
        index=True,
    )

    estimated_start_date = Column(Date, nullable=True)
    estimated_start_period = Column(String(10), nullable=True)
    estimated_end_date = Column(Date, nullable=True)
    estimated_end_period = Column(String(10), nullable=True)

    accepted_at = Column(TIMESTAMP(timezone=True), nullable=True)
    started_at = Column(TIMESTAMP(timezone=True), nullable=True)
    completed_at = Column(TIMESTAMP(timezone=True), nullable=True)

    service_summary = Column(Text, nullable=True)
    cancel_reason = Column(Text, nullable=True)

    source_type = Column(Enum(SourceType, native_enum=False), nullable=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=True, index=True)
    opportunity_id = Column(
        Integer, ForeignKey("opportunities.id"), nullable=True, index=True
    )
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True, index=True)

    created_at = Column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=True, index=True
    )
    updated_at = Column(TIMESTAMP(timezone=True), onupdate=func.now(), nullable=True)

    submitter = relationship(
        "User", foreign_keys=[submitter_id], back_populates="work_orders_as_submitter"
    )
    related_sales = relationship(
        "User", foreign_keys=[related_sales_id], back_populates="work_orders_as_sales"
    )
    channel = relationship("Channel", back_populates="work_orders")
    technicians = relationship("WorkOrderTechnician", back_populates="work_order")
    evaluation = relationship("Evaluation", back_populates="work_order", uselist=False)


class WorkOrderTechnician(Base):
    __tablename__ = "work_order_technicians"

    id = Column(Integer, primary_key=True, index=True)
    work_order_id = Column(
        Integer,
        ForeignKey("work_orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    technician_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=True
    )

    work_order = relationship("WorkOrder", back_populates="technicians")
    technician = relationship("User", back_populates="work_orders_as_technician")
