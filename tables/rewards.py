<<<<<<< HEAD
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from datetime import datetime
from config import Base

class Reward(Base):
    __tablename__ = "rewards"
    id = Column(Integer, primary_key=True)
    parent_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(120), nullable=False)
    description = Column(Text)
    cost = Column(Integer, nullable=False, default=0)
    image_path = Column(String)  # optional
    created_at = Column(DateTime, default=datetime.utcnow)
=======
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from config import Base
import datetime

class Rewards(Base):
    __tablename__ = 'rewards'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    description = Column(String)
    cost = Column(Integer, nullable=False)
    stock = Column(Integer, nullable=False)

    create_date = Column(DateTime, default=datetime.datetime.now)
    update_date = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)

class Redemptions(Base):
    __tablename__ = 'redemptions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    child_id = Column(Integer, ForeignKey("users.id"))
    reward_id = Column(Integer, ForeignKey("rewards.id"))
    status = Column(String, default="pending")   # pending, confirmed, rejected

    child = relationship("Users")
    reward = relationship("Rewards")

    create_date = Column(DateTime, default=datetime.datetime.now)
>>>>>>> 432795cabed0a2d0f3eb018c72e240796f945ea9
