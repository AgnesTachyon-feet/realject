from sqlalchemy import Column, Integer, String, DateTime
<<<<<<< HEAD
from sqlalchemy.dialects.postgresql import ENUM as PGEnum
=======
>>>>>>> sorrawichfeature
from config import Base
import enum
import datetime

class RoleEnum(enum.Enum):
    kid = "kid"
    parent = "parent"

class Users(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
<<<<<<< HEAD
    username = Column(String(50), nullable=False, unique=True)
    password = Column(String, nullable=False)
    first_name = Column(String(50), nullable=False)
    role = Column(
        PGEnum(RoleEnum, name="role_enum", create_type=True, validate_strings=True),
        nullable=False
    )

    create_date = Column(DateTime, default=datetime.datetime.utcnow)
    update_date = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
=======
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    email = Column(String, nullable=False)
    role = Column(String, nullable=False)   # parent / child
    points = Column(Integer, default=0)

    create_date = Column(DateTime, default=datetime.datetime.now)
    update_date = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)
>>>>>>> sorrawichfeature
