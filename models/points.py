"""
Schemas ของ Points และ History
- PointsOut: ใช้ตอบกลับจำนวนแต้มรวมของเด็ก
- PointsHistoryOut: ใช้ตอบกลับประวัติการได้แต้ม
"""

from pydantic import BaseModel
from datetime import datetime

class PointsOut(BaseModel):
    child_id: int
    total_points: int

class PointsHistoryOut(BaseModel):
    id: int
    child_id: int
    task_id: int | None
    points: int
    created_at: datetime

    class Config:
        orm_mode = True
