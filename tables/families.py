from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import ENUM as PGEnum
from config import Base
from tables.users import RoleEnum

class Family(Base):
    __tablename__ = "families"

    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False)
    code = Column(String(16), unique=True, nullable=False)
    owner_parent_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

class FamilyMember(Base):
    __tablename__ = "family_members"

    id = Column(Integer, primary_key=True)
    family_id = Column(Integer, ForeignKey("families.id", ondelete="CASCADE"), nullable=True)
    user_id   = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)

    role = Column(
        PGEnum(RoleEnum, name="role_enum", create_type=True, validate_strings=True),
        nullable=True
    )

    __table_args__ = (
        UniqueConstraint("family_id", "user_id", name="uq_family_user"),
    )