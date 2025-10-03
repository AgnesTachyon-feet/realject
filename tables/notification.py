"""
ตาราง Notification: เก็บแจ้งเตือนในระบบ (in-app)
ฟิลด์หลัก: user_id (ผู้รับแจ้ง), message (ข้อความ), is_read (สถานะ), created_at
"""

from sqlalchemy import Column, Integer, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from config import Base

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # ความสัมพันธ์กับ User
    user = relationship("User", back_populates="notifications")
