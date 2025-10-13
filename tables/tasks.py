from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum, Index
from datetime import datetime
import enum
from config import Base, now_th

class TaskStatus(str, enum.Enum):
    assigned = "assigned"
    submitted = "submitted"
    approved = "approved"
    rejected = "rejected"

class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True)
    title = Column(String(120), nullable=False)
    description = Column(Text)
    points = Column(Integer, nullable=False, default=0)
    parent_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    kid_id    = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status = Column(Enum(TaskStatus), nullable=False, default=TaskStatus.assigned)
    created_at = Column(DateTime(timezone=True), default=now_th)
    completed_at = Column(DateTime(timezone=True), nullable=True, index=True)
    __table_args__ = (Index("ix_task_kid_status", "kid_id", "status"),)