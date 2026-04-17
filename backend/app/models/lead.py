from sqlalchemy import Column, Integer, String, Date, Boolean, ForeignKey, DECIMAL, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship
from app.database import Base


class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    lead_code = Column(String(25), unique=True, nullable=False, index=True)
    lead_name = Column(String(255), nullable=False)
    terminal_customer_id = Column(
        Integer, ForeignKey("terminal_customers.id"), nullable=False
    )
    channel_id = Column(Integer, ForeignKey("channels.id"), nullable=True)
    source_channel_id = Column(
        Integer, ForeignKey("channels.id"), nullable=True, index=True
    )
    lead_stage = Column(String(30), nullable=False, default="初步接触")
    lead_source = Column(String(50))
    contact_person = Column(String(100))
    contact_phone = Column(String(20))
    products = Column(ARRAY(String(100)), default=[])
    estimated_budget = Column(DECIMAL(15, 2))
    has_confirmed_requirement = Column(Boolean, default=False)
    has_confirmed_budget = Column(Boolean, default=False)
    converted_to_opportunity = Column(Boolean, default=False)
    opportunity_id = Column(Integer, ForeignKey("opportunities.id"))
    sales_owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    notes = Column(Text)
    created_at = Column(Date)
    updated_at = Column(Date)

    terminal_customer = relationship("TerminalCustomer", back_populates="leads")
    channel = relationship("Channel", foreign_keys=[channel_id], back_populates="leads")
    source_channel = relationship(
        "Channel", foreign_keys=[source_channel_id], back_populates="source_leads"
    )
    sales_owner = relationship("User", back_populates="leads")
    opportunity = relationship("Opportunity", back_populates="source_lead")
    follow_ups = relationship("FollowUp", back_populates="lead")
