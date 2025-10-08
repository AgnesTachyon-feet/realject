"""
โมเดล Submission ใช้เก็บงานที่เด็กส่งเข้ามา
แต่ละ submission จะเชื่อมกับ task_id และ child_id
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from config import Base

class SubmissionStatus(enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"

class Submission(Base):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    child_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    evidence_path = Column(String(1024), nullable=True)
    message = Column(Text, nullable=True)
    status = Column(Enum(SubmissionStatus), default=SubmissionStatus.pending, nullable=False)
    submitted_at = Column(DateTime, default=datetime.utcnow)
    reviewed_at = Column(DateTime, nullable=True)

    task = relationship("Task", back_populates="submissions")