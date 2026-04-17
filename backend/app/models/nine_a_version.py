from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    ForeignKey,
    DECIMAL,
    DateTime,
    Date,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class NineAVersion(Base):
    __tablename__ = "nine_a_versions"

    id = Column(Integer, primary_key=True, index=True)
    opportunity_id = Column(
        Integer,
        ForeignKey("opportunities.id", ondelete="CASCADE"),
        nullable=False,
    )
    version_number = Column(Integer, nullable=False, default=1)

    key_events = Column(Text)
    budget = Column(DECIMAL(15, 2))
    decision_chain_influence = Column(Text)
    customer_challenges = Column(Text)
    customer_needs = Column(Text)
    solution_differentiation = Column(Text)
    competitors = Column(Text)
    buying_method = Column(Text)
    close_date = Column(Date)

    created_at = Column(DateTime, server_default=func.now())
    created_by_id = Column(Integer, ForeignKey("users.id"))

    opportunity = relationship("Opportunity")
    created_by = relationship("User")
