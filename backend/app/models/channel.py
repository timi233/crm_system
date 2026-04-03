from sqlalchemy import Column, Integer, String, Text, Date, DECIMAL
from sqlalchemy.orm import relationship
from app.database import Base


class Channel(Base):
    __tablename__ = "channels"

    id = Column(Integer, primary_key=True, index=True)
    channel_code = Column(String(30), unique=True, nullable=False, index=True)
    company_name = Column(String(255), nullable=False)
    channel_type = Column(String(30), nullable=False)
    status = Column(String(20), default="合作中")

    main_contact = Column(String(100))
    phone = Column(String(20))
    email = Column(String(100))

    province = Column(String(50))
    city = Column(String(50))
    address = Column(String(255))

    credit_code = Column(String(18))
    bank_name = Column(String(100))
    bank_account = Column(String(50))

    website = Column(String(255))
    wechat = Column(String(100))

    cooperation_products = Column(Text)
    cooperation_region = Column(String(255))
    discount_rate = Column(DECIMAL(5, 4))

    billing_info = Column(Text)
    notes = Column(Text)
    created_at = Column(Date)
    updated_at = Column(Date)

    opportunities = relationship("Opportunity", back_populates="channel")
    projects = relationship("Project", back_populates="channel")
    contracts = relationship("Contract", back_populates="channel")
    terminal_customers = relationship("TerminalCustomer", back_populates="channel")
