from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class EntityProduct(Base):
    __tablename__ = "entity_products"

    id = Column(Integer, primary_key=True, index=True)
    entity_type = Column(String(20), nullable=False)  # lead, opportunity, project
    entity_id = Column(Integer, nullable=False)
    product_type_id = Column(Integer, ForeignKey("dict_items.id"))
    brand_id = Column(Integer, ForeignKey("dict_items.id"), nullable=True)
    model_id = Column(Integer, ForeignKey("dict_items.id"), nullable=True)
    created_at = Column(Date)

    product_type = relationship("DictItem", foreign_keys=[product_type_id])
    brand = relationship("DictItem", foreign_keys=[brand_id])
    model = relationship("DictItem", foreign_keys=[model_id])
