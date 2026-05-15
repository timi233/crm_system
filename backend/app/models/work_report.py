from sqlalchemy import Column, Integer, String, Date, Text, TIMESTAMP, JSON, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class WorkReport(Base):
    __tablename__ = "work_reports"

    id = Column(Integer, primary_key=True, index=True)
    report_type = Column(String(20), nullable=False)
    report_date = Column(Date, nullable=False)
    week_start = Column(Date, nullable=True)
    week_end = Column(Date, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    owner_role = Column(String(50), nullable=True)
    status = Column(String(20), default="draft", nullable=False)
    structured_snapshot = Column(JSON, nullable=True)
    remark = Column(Text, nullable=True)
    source_report_ids = Column(JSON, nullable=True)
    submitted_at = Column(TIMESTAMP(timezone=True), nullable=True)
    withdrawn_at = Column(TIMESTAMP(timezone=True), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=True)
    updated_at = Column(TIMESTAMP(timezone=True), onupdate=func.now(), nullable=True)

    __table_args__ = (
        UniqueConstraint("owner_id", "report_type", "report_date", name="uq_work_report_owner_type_date"),
    )

    owner = relationship("User", backref="work_reports")