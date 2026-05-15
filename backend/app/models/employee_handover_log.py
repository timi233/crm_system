from sqlalchemy import Column, Integer, String, TIMESTAMP, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class HandoverLogOperation:
    TRANSFER = "transfer"
    ANNOTATE = "annotate"


class EmployeeHandoverLog(Base):
    __tablename__ = "employee_handover_logs"

    id = Column(Integer, primary_key=True, index=True)
    handover_request_id = Column(Integer, ForeignKey("employee_handover_requests.id"), nullable=False)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(Integer, nullable=False)
    field_name = Column(String(50), nullable=False)
    from_user_id = Column(Integer, nullable=True)
    to_user_id = Column(Integer, nullable=True)
    operation = Column(String(20), default=HandoverLogOperation.TRANSFER, nullable=False)
    remark_appended = Column(Text, nullable=True)
    executed_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=True)

    handover_request = relationship("EmployeeHandoverRequest", back_populates="logs")