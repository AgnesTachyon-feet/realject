from sqlalchemy import Column, Integer, String, Enum, DateTime
from datetime import datetime
import enum
from config import Base

class RoleEnum(str, enum.Enum):
    kid = "kid"
    parent = "parent"

class Users(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(Enum(RoleEnum), nullable=False)
    points = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)