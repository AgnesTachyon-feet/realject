"""
Schemas ของ Submission สำหรับ validate input/output
"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class SubmissionCreate(BaseModel):
    task_id: int
    child_id: int
    message: Optional[str] = None

class SubmissionDecision(BaseModel):
    parent_id: int
    approve: bool
    comment: Optional[str] = None

class SubmissionOut(BaseModel):
    id: int
    task_id: int
    child_id: int
    evidence_path: Optional[str]
    message: Optional[str]
    status: str
    submitted_at: datetime
    reviewed_at: Optional[datetime]

    class Config:
        orm_mode = True
