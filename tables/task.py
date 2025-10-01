"""
ไฟล์นี้ประกาศ ORM Model สำหรับตาราง Tasks
ตารางนี้เก็บข้อมูลภารกิจที่ผู้ปกครองสร้างและมอบหมายให้เด็ก
ฟิลด์ประกอบด้วย title, description, due_date, points และความสัมพันธ์กับผู้ใช้
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from config import Base

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    due_date = Column(DateTime, nullable=True)
    points = Column(Integer, default=0, nullable=False)

    parent_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    child_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    # ความสัมพันธ์กับ User (parent และ child)
    parent = relationship("User", foreign_keys=[parent_id])
    child = relationship("User", foreign_keys=[child_id])
    '''ต้องทำให้มัน foreign ให้ได้'''