from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from config import Base


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    due_date = Column(DateTime)
    points = Column(Integer, default=0, nullable=False)

    parent_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    kid_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    # 🔗 ความสัมพันธ์กับ Users
    parent = relationship(
        "Users",                # ชื่อ class ใน users.py
        foreign_keys=[parent_id],
        back_populates="tasks_created"
    )
    kid = relationship(
        "Users",
        foreign_keys=[kid_id],
        back_populates="tasks_assigned"
    )
