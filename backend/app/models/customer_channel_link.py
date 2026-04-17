from sqlalchemy import (
    Column,
    Integer,
    String,
    Date,
    Text,
    DECIMAL,
    TIMESTAMP,
    ForeignKey,
    Index,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class CustomerChannelLink(Base):
    __tablename__ = "customer_channel_links"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(
        Integer, ForeignKey("terminal_customers.id"), nullable=False, index=True
    )
    channel_id = Column(Integer, ForeignKey("channels.id"), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # '主渠道', '协作渠道', '历史渠道'
    discount_rate = Column(DECIMAL(5, 4), nullable=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    customer = relationship("TerminalCustomer", back_populates="channel_links")
    channel = relationship("Channel")
    creator = relationship("User", foreign_keys=[created_by])
