from sqlalchemy import Column, Integer, String, Float, ForeignKey, Date
from sqlalchemy.orm import relationship
from app.database import Base


class SalesTarget(Base):
    __tablename__ = "sales_targets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    target_type = Column(String(20), nullable=False)
    target_year = Column(Integer, nullable=False)
    target_period = Column(Integer, nullable=False)
    target_amount = Column(Float, nullable=False)
    parent_id = Column(Integer, ForeignKey("sales_targets.id"), nullable=True)
    created_at = Column(Date)
    updated_at = Column(Date)

    user = relationship("User", back_populates="sales_targets")
    parent = relationship("SalesTarget", remote_side=[id], backref="children")
