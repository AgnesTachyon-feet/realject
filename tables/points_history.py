"""
โมเดล PointsHistory: ใช้เก็บประวัติการได้รับแต้มของเด็ก
- child_id: อ้างอิงผู้ใช้ที่เป็นเด็ก
- task_id: งานที่เกี่ยวข้อง (ถ้ามี)
- points: จำนวนแต้มที่ได้รับ
- created_at: วันที่และเวลาที่ได้รับแต้ม
"""

from sqlalchemy import Column, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from config import Base

class PointsHistory(Base):
    __tablename__ = "points_history"

    id = Column(Integer, primary_key=True, index=True)
    child_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    points = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    child = relationship("User", back_populates="points_history")