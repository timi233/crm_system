from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text, DateTime
from app.database import Base


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    notification_type = Column(String(30), nullable=False)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    entity_type = Column(String(30))
    entity_id = Column(Integer)
    entity_code = Column(String(50))
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, nullable=False)
    read_at = Column(DateTime)
