from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.dialects.postgresql import ENUM as PGEnum
from config import Base
import enum
import datetime

class RoleEnum(enum.Enum):
    kid = "kid"
    parent = "parent"

class Users(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    first_name = Column(String, nullable=False)
    role = Column(
        PGEnum(RoleEnum, name="role_enum", create_type=True, validate_strings=True),
        nullable=False
    )

    create_date = Column(DateTime, default=datetime.datetime.utcnow)
    update_date = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
