from sqlalchemy import Column, Integer, String, Date, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class TerminalCustomer(Base):
    __tablename__ = "terminal_customers"

    id = Column(Integer, primary_key=True, index=True)
    customer_code = Column(String(20), unique=True, nullable=False, index=True)
    customer_name = Column(String(255), nullable=False)
    credit_code = Column(String(18), nullable=False)
    customer_industry = Column(String(50), nullable=False)
    customer_region = Column(String(100), nullable=False)
    customer_owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    channel_id = Column(Integer, ForeignKey("channels.id"), nullable=True)
    main_contact = Column(String(100))
    phone = Column(String(20))
    customer_status = Column(String(20), nullable=False)
    maintenance_expiry = Column(Date)
    notes = Column(Text)

    owner = relationship("User", back_populates="terminal_customers")
    channel = relationship("Channel", back_populates="terminal_customers")
    opportunities = relationship("Opportunity", back_populates="terminal_customer")
    projects = relationship("Project", back_populates="terminal_customer")
    follow_ups = relationship("FollowUp", back_populates="terminal_customer")
    leads = relationship("Lead", back_populates="terminal_customer")
    contracts = relationship("Contract", back_populates="terminal_customer")
    product_installations = relationship(
        "ProductInstallation", back_populates="customer", cascade="all, delete-orphan"
    )
    channel_links = relationship("CustomerChannelLink", back_populates="customer")
