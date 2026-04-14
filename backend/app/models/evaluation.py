from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, ForeignKey, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class Evaluation(Base):
    __tablename__ = "evaluations"

    id = Column(Integer, primary_key=True, index=True)
    work_order_id = Column(
        Integer, ForeignKey("work_orders.id"), unique=True, nullable=False, index=True
    )

    quality_rating = Column(Integer, nullable=False)
    response_rating = Column(Integer, nullable=False)
    customer_feedback = Column(Text, nullable=True)
    improvement_suggestion = Column(Text, nullable=True)
    recommend = Column(Boolean, default=False, nullable=False)

    evaluator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=True
    )

    work_order = relationship("WorkOrder", back_populates="evaluation")
    evaluator = relationship("User")
