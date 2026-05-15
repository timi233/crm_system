from sqlalchemy import Column, Integer, String, TIMESTAMP, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class WorkReportComment(Base):
    __tablename__ = "work_report_comments"

    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("work_reports.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=True)

    report = relationship("WorkReport", backref="comments")
    user = relationship("User")
