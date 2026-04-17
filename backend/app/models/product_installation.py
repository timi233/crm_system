from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Date,
    TIMESTAMP,
    ForeignKey,
    CheckConstraint,
    Index,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class ProductInstallation(Base):
    __tablename__ = "product_installations"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(
        Integer, ForeignKey("terminal_customers.id", ondelete="CASCADE"), nullable=False
    )

    manufacturer = Column(String(100), nullable=False)
    product_type = Column(String(100), nullable=False)
    product_model = Column(String(100), nullable=True)
    license_scale = Column(String(100), nullable=True)
    system_version = Column(String(100), nullable=True)
    online_date = Column(Date, nullable=True)
    maintenance_expiry = Column(Date, nullable=True)

    username = Column(String(255), nullable=True)
    password = Column(String(255), nullable=True)
    login_url = Column(String(255), nullable=True)

    notes = Column(Text, nullable=True)

    created_at = Column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    created_by_id = Column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    __table_args__ = (
        Index("idx_pi_customer", "customer_id"),
        Index("idx_pi_manufacturer", "manufacturer"),
        Index("idx_pi_online_date", "online_date"),
        CheckConstraint(
            "manufacturer IN ('爱数', '安恒', 'IPG', '绿盟', '深信服', '其他')",
            name="check_manufacturer",
        ),
    )

    customer = relationship("TerminalCustomer", back_populates="product_installations")
    created_by = relationship("User", back_populates="product_installations")

    def __repr__(self):
        return (
            f"<ProductInstallation(id={self.id}, manufacturer='{self.manufacturer}')>"
        )
