from sqlalchemy import Column, Integer, String, Boolean, Text
from sqlalchemy.orm import relationship
from app.database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    product_code = Column(String(10), unique=True, nullable=False, index=True)
    product_name = Column(String(100), nullable=False)
    product_type = Column(String(30), nullable=False)
    brand_manufacturer = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)
    notes = Column(Text)
