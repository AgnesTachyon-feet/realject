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
