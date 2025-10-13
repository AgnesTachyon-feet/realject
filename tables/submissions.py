from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum
from datetime import datetime
import enum
from config import Base, now_th

class SubmissionStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"

class Submission(Base):
    __tablename__ = "submissions"
    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    kid_id  = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    message = Column(Text)
    evidence_path = Column(String)
    status = Column(Enum(SubmissionStatus), nullable=False, default=SubmissionStatus.pending)
    created_at = Column(DateTime(timezone=True), default=now_th)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)