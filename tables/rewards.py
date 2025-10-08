from sqlalchemy import Column, Integer, String, Text
from config import Base

class Reward(Base):
    __tablename__ = "rewards"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    cost = Column(Integer, nullable=False)
    image_path = Column(String)
