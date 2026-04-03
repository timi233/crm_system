from sqlalchemy import Column, Integer, String, Boolean, Integer, Text
from app.database import Base


class AlertRule(Base):
    __tablename__ = "alert_rules"

    id = Column(Integer, primary_key=True, index=True)
    rule_code = Column(String(50), unique=True, nullable=False)
    rule_name = Column(String(100), nullable=False)
    rule_type = Column(String(30), nullable=False)
    entity_type = Column(String(30), nullable=False)
    priority = Column(String(10), nullable=False, default="medium")
    threshold_days = Column(Integer, default=0)
    threshold_amount = Column(Integer, default=0)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(String(30))
    updated_at = Column(String(30))
