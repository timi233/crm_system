from sqlalchemy import Column, Integer, String, Date
from app.database import Base


class AutoNumber(Base):
    __tablename__ = "auto_numbers"

    id = Column(Integer, primary_key=True, index=True)
    entity_type = Column(String(20), unique=True, nullable=False, index=True)
    seq_date = Column(Date, nullable=False)
    current_seq = Column(Integer, default=0)
