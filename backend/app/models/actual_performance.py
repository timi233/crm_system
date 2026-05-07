from sqlalchemy import Column, Integer, Float, ForeignKey, TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class ActualPerformance(Base):
    __tablename__ = "actual_performance"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    target_id = Column(Integer, ForeignKey("sales_targets.id"), nullable=True)
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    amount_actual = Column(Float, default=0.0, nullable=True)
    gross_profit_actual = Column(Float, default=0.0, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=True)
    updated_at = Column(TIMESTAMP(timezone=True), onupdate=func.now(), nullable=True)

    user = relationship("User", backref="actual_performances")
    target = relationship("SalesTarget", backref="actual_performances")
