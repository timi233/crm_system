from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from app.database import Base


class UserNotificationRead(Base):
    __tablename__ = "user_notification_reads"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    entity_type = Column(String(30), nullable=False)
    entity_id = Column(Integer, nullable=False)
    notification_type = Column(String(30), nullable=False)
    created_at = Column(DateTime, nullable=False)
