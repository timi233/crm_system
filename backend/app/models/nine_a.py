from sqlalchemy import Column, Integer, String, Text, ForeignKey, DECIMAL, Date
from sqlalchemy.orm import relationship
from app.database import Base


class NineA(Base):
    __tablename__ = "nine_a"

    id = Column(Integer, primary_key=True, index=True)
    opportunity_id = Column(
        Integer,
        ForeignKey("opportunities.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )

    key_events = Column(Text)
    budget = Column(DECIMAL(15, 2))
    decision_chain_influence = Column(Text)
    customer_challenges = Column(Text)
    customer_needs = Column(Text)
    solution_differentiation = Column(Text)
    competitors = Column(Text)
    buying_method = Column(Text)
    close_date = Column(Date)

    opportunity = relationship("Opportunity", back_populates="nine_a")
