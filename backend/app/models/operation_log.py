"""
Operation Log model for tracking user actions.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, ForeignKey, TIMESTAMP, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from app.database import Base


class OperationLog(Base):
    __tablename__ = "operation_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user_name = Column(String(100), nullable=False)
    action_type = Column(
        String(30), nullable=False
    )  # CREATE, UPDATE, DELETE, CONVERT, STAGE_CHANGE
    entity_type = Column(
        String(30), nullable=False
    )  # customer, lead, opportunity, project, contract, channel, follow_up
    entity_id = Column(Integer, nullable=False)
    entity_code = Column(String(30))
    entity_name = Column(String(255))
    old_value = Column(JSONB)
    new_value = Column(JSONB)
    description = Column(Text)
    ip_address = Column(String(45))
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    user = relationship("User", backref="operation_logs")

    __table_args__ = (
        Index("idx_logs_user", "user_id"),
        Index("idx_logs_entity", "entity_type", "entity_id"),
        Index("idx_logs_action", "action_type"),
        Index("idx_logs_time", "created_at"),
    )


# Action type constants
ACTION_CREATE = "CREATE"
ACTION_UPDATE = "UPDATE"
ACTION_DELETE = "DELETE"
ACTION_CONVERT = "CONVERT"
ACTION_STAGE_CHANGE = "STAGE_CHANGE"
ACTION_STATUS_CHANGE = "STATUS_CHANGE"

# Entity type constants
ENTITY_CUSTOMER = "customer"
ENTITY_LEAD = "lead"
ENTITY_OPPORTUNITY = "opportunity"
ENTITY_PROJECT = "project"
ENTITY_CONTRACT = "contract"
ENTITY_CHANNEL = "channel"
ENTITY_FOLLOW_UP = "follow_up"
