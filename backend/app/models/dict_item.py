from sqlalchemy import Column, Integer, String, Boolean, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class DictItem(Base):
    __tablename__ = "dict_items"

    id = Column(Integer, primary_key=True, index=True)
    dict_type = Column(String(50), nullable=False, index=True)
    code = Column(String(50), nullable=False)
    name = Column(String(100), nullable=False)
    parent_id = Column(Integer, ForeignKey("dict_items.id"), nullable=True)
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    extra_data = Column(JSON, nullable=True)

    parent = relationship("DictItem", remote_side=[id], backref="children")
