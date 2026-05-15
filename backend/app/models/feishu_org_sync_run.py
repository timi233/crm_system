from sqlalchemy import Column, Integer, String, TIMESTAMP, Text, ForeignKey
from sqlalchemy.sql import func
from app.database import Base


class FeishuOrgSyncRun(Base):
    __tablename__ = "feishu_org_sync_runs"

    id = Column(Integer, primary_key=True, index=True)
    started_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=True)
    completed_at = Column(TIMESTAMP(timezone=True), nullable=True)
    status = Column(String(20), default="running", nullable=False)
    total_seen = Column(Integer, default=0, nullable=True)
    created_count = Column(Integer, default=0, nullable=True)
    updated_count = Column(Integer, default=0, nullable=True)
    left_detected_count = Column(Integer, default=0, nullable=True)
    trigger = Column(String(20), default="manual", nullable=False)
    triggered_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    error_message = Column(Text, nullable=True)