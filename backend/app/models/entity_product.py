from sqlalchemy import Column, Integer, String, Date, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class EntityProduct(Base):
    __tablename__ = "entity_products"

    id = Column(Integer, primary_key=True, index=True)
    entity_type = Column(String(20), nullable=False)  # lead, opportunity, project
    entity_id = Column(Integer, nullable=False)
    product_type_id = Column(Integer, ForeignKey("dict_items.id"))
    brand_id = Column(Integer, ForeignKey("dict_items.id"), nullable=True)
    model_id = Column(Integer, ForeignKey("dict_items.id"), nullable=True)
    quantity = Column(Integer, nullable=True, default=1)
    unit_price = Column(Numeric(precision=10, scale=2), nullable=True, default=0.00)
    created_at = Column(Date, server_default=func.current_date(), nullable=False)

    product_type = relationship("DictItem", foreign_keys=[product_type_id])
    brand = relationship("DictItem", foreign_keys=[brand_id])
    model = relationship("DictItem", foreign_keys=[model_id])
