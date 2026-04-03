from sqlalchemy import (
    Column,
    Integer,
    String,
    Date,
    DECIMAL,
    Text,
    ForeignKey,
    CheckConstraint,
    ARRAY,
)
from sqlalchemy.orm import relationship
from app.database import Base


class Opportunity(Base):
    __tablename__ = "opportunities"

    id = Column(Integer, primary_key=True, index=True)
    opportunity_code = Column(String(20), unique=True, nullable=False, index=True)
    opportunity_name = Column(String(255), nullable=False)
    terminal_customer_id = Column(
        Integer, ForeignKey("terminal_customers.id"), nullable=False
    )
    opportunity_source = Column(String(50), nullable=False)
    product_ids = Column(ARRAY(Integer))
    opportunity_stage = Column(String(30), nullable=False)
    lead_grade = Column(String(10), nullable=False)
    expected_contract_amount = Column(DECIMAL(15, 2), nullable=False)
    expected_close_date = Column(Date)
    sales_owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    channel_id = Column(Integer, ForeignKey("channels.id"))
    vendor_registration_status = Column(String(30))
    vendor_discount = Column(DECIMAL(5, 4))
    loss_reason = Column(String(100))
    project_id = Column(Integer, ForeignKey("projects.id"))
    created_at = Column(Date)

    terminal_customer = relationship("TerminalCustomer", back_populates="opportunities")
    sales_owner = relationship("User", back_populates="opportunities")
    channel = relationship("Channel", back_populates="opportunities")
    follow_ups = relationship("FollowUp", back_populates="opportunity")
    source_lead = relationship("Lead", back_populates="opportunity")
    nine_a = relationship("NineA", back_populates="opportunity", uselist=False)

    __table_args__ = (
        CheckConstraint(
            "(opportunity_stage <> 'Lost') OR (loss_reason IS NOT NULL)",
            name="chk_loss_reason",
        ),
    )
