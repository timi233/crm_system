from sqlalchemy import Column, Integer, String, Date, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class FollowUp(Base):
    __tablename__ = "follow_ups"

    id = Column(Integer, primary_key=True, index=True)
    terminal_customer_id = Column(Integer, ForeignKey("terminal_customers.id"))
    lead_id = Column(Integer, ForeignKey("leads.id"))
    opportunity_id = Column(Integer, ForeignKey("opportunities.id"))
    project_id = Column(Integer, ForeignKey("projects.id"))
    channel_id = Column(Integer, ForeignKey("channels.id"), nullable=True, index=True)

    # 新增字段：跟进类型区分
    follow_up_type = Column(String(20), nullable=False, default="business")

    follow_up_date = Column(Date, nullable=False)
    follow_up_method = Column(String(30), nullable=False)
    follow_up_content = Column(Text, nullable=False)

    # 放宽约束：跟进结论可为空
    follow_up_conclusion = Column(String(30), nullable=True)

    next_action = Column(String(255))
    next_follow_up_date = Column(Date)
    follower_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(Date)

    # 新增字段：渠道拜访专用
    visit_location = Column(String(100), nullable=True)  # 拜访地点
    visit_attendees = Column(String(255), nullable=True)  # 参与人员
    visit_purpose = Column(String(100), nullable=True)  # 拜访目的

    terminal_customer = relationship("TerminalCustomer", back_populates="follow_ups")
    lead = relationship("Lead", back_populates="follow_ups")
    opportunity = relationship("Opportunity", back_populates="follow_ups")
    project = relationship("Project", back_populates="follow_ups")
    channel = relationship("Channel", back_populates="follow_ups")
    follower = relationship("User", back_populates="follow_ups")
