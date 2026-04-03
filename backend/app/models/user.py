from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=True)
    hashed_password = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    role = Column(String, default="sales", nullable=False)
    name = Column(String, nullable=True)
    feishu_id = Column(String, unique=True, index=True, nullable=True)
    phone = Column(String, nullable=True)
    avatar = Column(Text, nullable=True)
    sales_leader_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    sales_region = Column(String, nullable=True)
    sales_product_line = Column(String, nullable=True)

    sales_leader = relationship("User", remote_side=[id], backref="sales_team")
    terminal_customers = relationship("TerminalCustomer", back_populates="owner")
    opportunities = relationship("Opportunity", back_populates="sales_owner")
    projects = relationship("Project", back_populates="sales_owner")
    follow_ups = relationship("FollowUp", back_populates="follower")
    leads = relationship("Lead", back_populates="sales_owner")
    sales_targets = relationship("SalesTarget", back_populates="user")
