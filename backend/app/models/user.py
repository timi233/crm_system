from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import uuid


class User(Base):
    __tablename__ = "users"

    # 原有字段（保持兼容）
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=True)
    hashed_password = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    role = Column(
        String, default="sales", nullable=False
    )  # 扩展: admin/sales/tech/channel_manager
    name = Column(String, nullable=True)
    feishu_id = Column(String, unique=True, index=True, nullable=True)
    phone = Column(String, nullable=True)
    avatar = Column(Text, nullable=True)
    sales_leader_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    sales_region = Column(String, nullable=True)
    sales_product_line = Column(String, nullable=True)

    # 新增：跨系统兼容字段
    uuid_id = Column(
        UUID(as_uuid=True), unique=True, index=True, nullable=True, default=None
    )  # 渠道系统UUID兼容
    cuid_id = Column(
        String(255), unique=True, index=True, nullable=True
    )  # 派工系统cuid兼容

    # 新增：派工系统角色字段
    functional_role = Column(String(50), nullable=True)  # TECHNICIAN/SALES/null
    responsibility_role = Column(
        String(50), nullable=True
    )  # SYSTEM_ADMIN/ADMIN/AUDITOR/OTHER/null
    department = Column(String(100), nullable=True)  # 部门
    user_status = Column(
        String(20), default="ACTIVE", nullable=True
    )  # ACTIVE/DISABLED (派工系统状态)

    # 新增：审计字段（渠道系统兼容）
    created_at = Column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=True
    )
    updated_at = Column(TIMESTAMP(timezone=True), onupdate=func.now(), nullable=True)
    full_name = Column(String(255), nullable=True)  # 渠道系统full_name兼容

    # 原有关系
    sales_leader = relationship("User", remote_side=[id], backref="sales_team")
    terminal_customers = relationship("TerminalCustomer", back_populates="owner")
    opportunities = relationship("Opportunity", back_populates="sales_owner")
    projects = relationship("Project", back_populates="sales_owner")
    follow_ups = relationship("FollowUp", back_populates="follower")
    leads = relationship("Lead", back_populates="sales_owner")
    sales_targets = relationship("SalesTarget", back_populates="user")

    # 新增关系：渠道分配、执行计划、工单
    channel_assignments = relationship(
        "ChannelAssignment",
        foreign_keys="ChannelAssignment.user_id",
        back_populates="user",
    )
    execution_plans = relationship("ExecutionPlan", back_populates="user")
    work_orders_as_submitter = relationship(
        "WorkOrder", foreign_keys="WorkOrder.submitter_id", back_populates="submitter"
    )
    work_orders_as_sales = relationship(
        "WorkOrder",
        foreign_keys="WorkOrder.related_sales_id",
        back_populates="related_sales",
    )
    work_orders_as_technician = relationship(
        "WorkOrderTechnician", back_populates="technician"
    )
