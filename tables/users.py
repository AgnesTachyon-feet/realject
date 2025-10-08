from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.dialects.postgresql import ENUM as PGEnum
import enum
from config import Base
import datetime

class RoleEnum(enum.Enum):
    kid = "kid"
    parent = "parent"

class Users(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    phone_number = Column(String, nullable=False, unique=True)

    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)

    role = Column(PGEnum(RoleEnum, name="role_enum",create_type=True, validate_strings=True), nullable=False)

    create_date = Column(DateTime, default = datetime.datetime.now())
    update_date = Column(DateTime, onupdate=datetime.datetime.now())