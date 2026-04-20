from sqlalchemy import Column, Integer, String, Date, DECIMAL, Text, ForeignKey, ARRAY
from sqlalchemy.orm import relationship
from app.database import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    project_code = Column(String(25), unique=True, nullable=False, index=True)
    project_name = Column(String(255), nullable=False)
    terminal_customer_id = Column(
        Integer, ForeignKey("terminal_customers.id"), nullable=False
    )
    channel_id = Column(Integer, ForeignKey("channels.id"))
    source_opportunity_id = Column(Integer, ForeignKey("opportunities.id"))
    product_ids = Column(ARRAY(Integer), nullable=False, default=[])
    products = Column(ARRAY(String(100)), default=[])
    business_type = Column(String(30), nullable=False)
    project_status = Column(String(30), nullable=False)
    sales_owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    downstream_contract_amount = Column(DECIMAL(15, 2), nullable=False)
    upstream_procurement_amount = Column(DECIMAL(15, 2))
    direct_project_investment = Column(DECIMAL(15, 2))
    additional_investment = Column(DECIMAL(15, 2))
    winning_date = Column(Date)
    acceptance_date = Column(Date)
    first_payment_date = Column(Date)
    actual_payment_amount = Column(DECIMAL(15, 2))
    notes = Column(Text)
    gross_margin = Column(DECIMAL(15, 2))

    terminal_customer = relationship("TerminalCustomer", back_populates="projects")
    channel = relationship("Channel", back_populates="projects")
    source_opportunity = relationship(
        "Opportunity", back_populates=None, foreign_keys=[source_opportunity_id]
    )
    sales_owner = relationship("User", back_populates="projects")
    follow_ups = relationship("FollowUp", back_populates="project")
    contracts = relationship("Contract", back_populates="project")
