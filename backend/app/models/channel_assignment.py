from sqlalchemy import Column, Integer, String, TIMESTAMP, ForeignKey, Boolean, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class PermissionLevel(enum.Enum):
    read = "read"
    write = "write"
    admin = "admin"


class ChannelAssignment(Base):
    __tablename__ = "channel_assignments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    channel_id = Column(Integer, ForeignKey("channels.id"), nullable=False, index=True)
    permission_level = Column(
        Enum(PermissionLevel, native_enum=False),
        nullable=False,
        default=PermissionLevel.read,
    )
    assigned_at = Column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=True
    )
    assigned_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    target_responsibility = Column(Boolean, default=False, nullable=False)
    created_at = Column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=True
    )
    updated_at = Column(TIMESTAMP(timezone=True), onupdate=func.now(), nullable=True)

    user = relationship(
        "User", foreign_keys=[user_id], back_populates="channel_assignments"
    )
    channel = relationship("Channel", back_populates="channel_assignments")
    assigner = relationship("User", foreign_keys=[assigned_by])
