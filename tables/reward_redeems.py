from sqlalchemy import Column, Integer, DateTime, Enum, ForeignKey
from datetime import datetime
import enum
from config import Base

class RedeemStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"

class RewardRedeem(Base):
    __tablename__ = "reward_redeems"
    id = Column(Integer, primary_key=True)
    reward_id = Column(Integer, ForeignKey("rewards.id"), nullable=False)
    kid_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(Enum(RedeemStatus), default=RedeemStatus.pending)
    created_at = Column(DateTime, default=datetime.utcnow)
    reviewed_at = Column(DateTime)
