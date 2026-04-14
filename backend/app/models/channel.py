from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Date,
    DECIMAL,
    TIMESTAMP,
    ForeignKey,
    Enum,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class BusinessType(enum.Enum):
    basic = "basic"
    high_value = "high-value"
    pending_signup = "pending-signup"


class ChannelStatus(enum.Enum):
    active = "active"
    inactive = "inactive"
    suspended = "suspended"


class Channel(Base):
    __tablename__ = "channels"

    # 原有字段（销管系统）
    id = Column(Integer, primary_key=True, index=True)
    channel_code = Column(String(30), unique=True, nullable=False, index=True)
    company_name = Column(String(255), nullable=False)
    channel_type = Column(String(30), nullable=False)
    status = Column(String(20), default="合作中")

    main_contact = Column(String(100))
    phone = Column(String(20))
    email = Column(String(100))

    province = Column(String(50))
    city = Column(String(50))
    address = Column(String(255))

    credit_code = Column(String(18))
    bank_name = Column(String(100))
    bank_account = Column(String(50))

    website = Column(String(255))
    wechat = Column(String(100))

    cooperation_products = Column(Text)
    cooperation_region = Column(String(255))
    discount_rate = Column(DECIMAL(5, 4))

    billing_info = Column(Text)
    notes = Column(Text)
    created_at_legacy = Column(Date)  # 原有created_at保留
    updated_at_legacy = Column(Date)  # 原有updated_at保留

    # 新增：渠道管理系统(QDmgt)兼容字段
    uuid_id = Column(UUID(as_uuid=True), unique=True, index=True, nullable=True)
    business_type = Column(Enum(BusinessType), nullable=True, index=True)
    channel_status = Column(Enum(ChannelStatus), nullable=True, index=True)
    description = Column(Text, nullable=True)
    contact_person = Column(String(100), nullable=True)
    contact_email = Column(String(255), nullable=True)
    contact_phone = Column(String(50), nullable=True)

    # 新增：审计字段
    created_at = Column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=True
    )
    updated_at = Column(TIMESTAMP(timezone=True), onupdate=func.now(), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    last_modified_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    # 原有关系
    opportunities = relationship("Opportunity", back_populates="channel")
    projects = relationship("Project", back_populates="channel")
    contracts = relationship("Contract", back_populates="channel")
    terminal_customers = relationship("TerminalCustomer", back_populates="channel")

    # 新增关系：渠道管理模块
    creator = relationship("User", foreign_keys=[created_by])
    last_modifier = relationship("User", foreign_keys=[last_modified_by])
    channel_assignments = relationship("ChannelAssignment", back_populates="channel")
    channel_targets = relationship("UnifiedTarget", back_populates="channel")
    execution_plans = relationship("ExecutionPlan", back_populates="channel")
    work_orders = relationship("WorkOrder", back_populates="channel")
