from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from config import Base

class Family(Base):
    __tablename__ = "families"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    code = Column(String, unique=True, nullable=False)
    owner_parent_id = Column(Integer, ForeignKey("users.id"), nullable=False)

class FamilyMember(Base):
    __tablename__ = "family_members"
    id = Column(Integer, primary_key=True)
    family_id = Column(Integer, ForeignKey("families.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(String, nullable=False)  # "parent" หรือ "kid"
    __table_args__ = (UniqueConstraint("family_id", "user_id", name="uq_family_user"),)
