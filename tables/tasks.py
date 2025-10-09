from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum
from datetime import datetime
import enum
from config import Base

class TaskStatus(str, enum.Enum):
    assigned = "assigned"
    submitted = "submitted"
    approved = "approved"
    rejected = "rejected"

class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    points = Column(Integer, default=0)
    parent_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    kid_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(Enum(TaskStatus), default=TaskStatus.assigned, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
