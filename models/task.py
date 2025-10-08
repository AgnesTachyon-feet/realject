"""
ไฟล์นี้ประกาศ Pydantic Schemas สำหรับ Task
Schema ใช้ validate ข้อมูลที่รับเข้ามา (input) และส่งกลับไป (output)
"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    points: int = 0
    parent_id: int
    child_id: int

class TaskOut(BaseModel):
    id: int
    title: str
    description: Optional[str]
    due_date: Optional[datetime]
    points: int
    parent_id: int
    child_id: int
    created_at: datetime

    class Config:
        orm_mode = True