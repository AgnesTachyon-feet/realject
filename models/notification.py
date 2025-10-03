"""
Models สำหรับ Notification ใช้ validate input/output
"""

from pydantic import BaseModel
from datetime import datetime

class NotificationOut(BaseModel):
    id: int
    message: str
    is_read: bool
    created_at: datetime

    class Config:
        orm_mode = True