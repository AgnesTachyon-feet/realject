from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from datetime import datetime
from config import Base

class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    points = Column(Integer, default=0)
    parent_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    kid_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
