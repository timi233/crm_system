from sqlalchemy import (
    Column,
    Integer,
    String,
    Date,
    DECIMAL,
    Text,
    ForeignKey,
    CheckConstraint,
)
from sqlalchemy.orm import relationship
from app.database import Base


class Contract(Base):
    __tablename__ = "contracts"

    id = Column(Integer, primary_key=True, index=True)
    contract_code = Column(String(30), unique=True, nullable=False, index=True)
    contract_name = Column(String(255), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    contract_direction = Column(String(20), nullable=False, default="Downstream")
    contract_status = Column(String(20), nullable=False, default="draft")

    terminal_customer_id = Column(Integer, ForeignKey("terminal_customers.id"))
    channel_id = Column(Integer, ForeignKey("channels.id"))

    contract_amount = Column(DECIMAL(15, 2), nullable=False, default=0)
    signing_date = Column(Date)
    effective_date = Column(Date)
    expiry_date = Column(Date)

    contract_file_url = Column(Text)
    notes = Column(Text)

    created_at = Column(Date)
    updated_at = Column(Date)

    project = relationship("Project", back_populates="contracts")
    terminal_customer = relationship("TerminalCustomer", back_populates="contracts")
    channel = relationship("Channel", back_populates="contracts")
    products = relationship(
        "ContractProduct", back_populates="contract", cascade="all, delete-orphan"
    )
    payment_plans = relationship(
        "PaymentPlan", back_populates="contract", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint(
            "contract_direction IN ('Downstream', 'Upstream')",
            name="chk_contract_direction",
        ),
        CheckConstraint(
            "contract_status IN ('draft', 'pending', 'signed', 'archived', 'rejected')",
            name="chk_contract_status",
        ),
    )


class ContractProduct(Base):
    __tablename__ = "contract_products"

    id = Column(Integer, primary_key=True, index=True)
    contract_id = Column(Integer, ForeignKey("contracts.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    product_name = Column(String(100), nullable=False)
    quantity = Column(DECIMAL(10, 2), nullable=False, default=1)
    unit_price = Column(DECIMAL(15, 2), nullable=False, default=0)
    discount = Column(DECIMAL(5, 4), default=1.0000)
    amount = Column(DECIMAL(15, 2), nullable=False, default=0)
    notes = Column(Text)

    contract = relationship("Contract", back_populates="products")
    product = relationship("Product")


class PaymentPlan(Base):
    __tablename__ = "payment_plans"

    id = Column(Integer, primary_key=True, index=True)
    contract_id = Column(Integer, ForeignKey("contracts.id"), nullable=False)
    plan_stage = Column(String(50), nullable=False)
    plan_amount = Column(DECIMAL(15, 2), nullable=False, default=0)
    plan_date = Column(Date)
    actual_amount = Column(DECIMAL(15, 2), default=0)
    actual_date = Column(Date)
    payment_status = Column(String(20), default="pending")
    notes = Column(Text)

    contract = relationship("Contract", back_populates="payment_plans")

    __table_args__ = (
        CheckConstraint(
            "payment_status IN ('pending', 'partial', 'completed')",
            name="chk_payment_status",
        ),
    )
