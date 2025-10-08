from sqlalchemy import Column, Integer, String, DateTime, JSON
from datetime import datetime
from config import Base

class SystemLog(Base):
    __tablename__ = "system_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    action = Column(String, nullable=False)
    actor_id = Column(Integer, nullable=False)
    target_table = Column(String, nullable=False)
    target_id = Column(Integer, nullable=False)
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
