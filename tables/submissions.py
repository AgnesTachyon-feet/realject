from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum
from datetime import datetime
import enum
from config import Base

class SubmissionStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"

class Submission(Base):
    __tablename__ = "submissions"
    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey("tasks.id"))
    kid_id = Column(Integer, ForeignKey("users.id"))
    message = Column(String)
    evidence_path = Column(String)
    status = Column(Enum(SubmissionStatus), default=SubmissionStatus.pending)
    created_at = Column(DateTime, default=datetime.utcnow)
    reviewed_at = Column(DateTime)
