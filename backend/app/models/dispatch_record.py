from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    TIMESTAMP,
    ForeignKey,
    CheckConstraint,
    Index,
)
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class DispatchRecord(Base):
    __tablename__ = "dispatch_records"

    id = Column(Integer, primary_key=True, index=True)
    work_order_id = Column(String(100), unique=True, nullable=False)
    work_order_no = Column(String(50))

    source_type = Column(String(20), nullable=False)
    lead_id = Column(
        Integer, ForeignKey("leads.id", ondelete="SET NULL"), nullable=True
    )
    opportunity_id = Column(
        Integer, ForeignKey("opportunities.id", ondelete="SET NULL"), nullable=True
    )
    project_id = Column(
        Integer, ForeignKey("projects.id", ondelete="SET NULL"), nullable=True
    )

    status = Column(String(50), nullable=False, server_default="pending")
    previous_status = Column(String(50))
    status_updated_at = Column(TIMESTAMP(timezone=True))

    order_type = Column(String(10))
    customer_name = Column(String(255))
    technician_ids = Column(ARRAY(Text))
    priority = Column(String(20))
    description = Column(Text)
    dispatch_data = Column(JSONB)

    created_at = Column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )
    dispatched_at = Column(TIMESTAMP(timezone=True))
    completed_at = Column(TIMESTAMP(timezone=True))

    __table_args__ = (
        CheckConstraint(
            "source_type IN ('lead', 'opportunity', 'project')",
            name="check_source_type",
        ),
        Index("idx_dispatch_lead", "lead_id", postgresql_where="lead_id IS NOT NULL"),
        Index(
            "idx_dispatch_opportunity",
            "opportunity_id",
            postgresql_where="opportunity_id IS NOT NULL",
        ),
        Index(
            "idx_dispatch_project",
            "project_id",
            postgresql_where="project_id IS NOT NULL",
        ),
        Index("idx_dispatch_status", "status"),
        Index("idx_dispatch_created_at", "created_at"),
    )

    def __repr__(self):
        return f"<DispatchRecord(id={self.id}, work_order_id='{self.work_order_id}', status='{self.status}')>"
