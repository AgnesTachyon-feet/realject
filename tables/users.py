from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.dialects.postgresql import ENUM as PGEnum
from config import Base, now_th
import enum, datetime

class RoleEnum(enum.Enum):
    kid = "kid"
    parent = "parent"

class Users(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), nullable=False, unique=True)
    password = Column(String, nullable=False)
    first_name = Column(String, nullable=False)
    role = Column(PGEnum(RoleEnum, name="role_enum", create_type=True, validate_strings=True), nullable=False)
    points = Column(Integer, nullable=False, default=0)
    create_date = Column(DateTime(timezone=True), default=now_th)
    update_date = Column(DateTime(timezone=True), default=now_th, onupdate=now_th)