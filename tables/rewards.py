from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from datetime import datetime
from config import Base, now_th

class Reward(Base):
    __tablename__ = "rewards"
    id = Column(Integer, primary_key=True)
    parent_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(120), nullable=False)
    description = Column(Text)
    cost = Column(Integer, nullable=False, default=0)
    image_path = Column(String)
    created_at = Column(DateTime(timezone=True), default=now_th)