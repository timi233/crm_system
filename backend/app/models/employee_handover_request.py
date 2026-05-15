from sqlalchemy import Column, Integer, String, TIMESTAMP, Text, ForeignKey, JSON, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class HandoverRequestStatus:
    PENDING_ASSIGNMENT = "pending_assignment"
    PENDING_EXECUTION = "pending_execution"
    EXECUTING = "executing"
    COMPLETED = "completed"
    CANCELED = "canceled"
    FAILED = "failed"


class EmployeeHandoverRequest(Base):
    __tablename__ = "employee_handover_requests"

    id = Column(Integer, primary_key=True, index=True)
    from_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    to_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    initiated_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    team_manager_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    sync_run_id = Column(Integer, ForeignKey("feishu_org_sync_runs.id"), nullable=True)
    status = Column(String(30), default=HandoverRequestStatus.PENDING_ASSIGNMENT, nullable=False)
    scope_config = Column(JSON, nullable=True)
    preview_summary = Column(JSON, nullable=True)
    execution_summary = Column(JSON, nullable=True)
    notification_id = Column(Integer, ForeignKey("notifications.id"), nullable=True)
    feishu_message_id = Column(String(100), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=True)
    decided_at = Column(TIMESTAMP(timezone=True), nullable=True)
    executed_at = Column(TIMESTAMP(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)

    from_user = relationship("User", foreign_keys=[from_user_id])
    to_user = relationship("User", foreign_keys=[to_user_id])
    initiated_by = relationship("User", foreign_keys=[initiated_by_user_id])
    team_manager = relationship("User", foreign_keys=[team_manager_user_id])
    notification = relationship("Notification")
    logs = relationship("EmployeeHandoverLog", back_populates="handover_request")