from sqlalchemy import Column, Integer, DateTime, ForeignKey, Enum
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
    reward_id = Column(Integer, ForeignKey("rewards.id", ondelete="CASCADE"), nullable=False)
    kid_id    = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status = Column(Enum(RedeemStatus), nullable=False, default=RedeemStatus.pending)
    created_at = Column(DateTime, default=datetime.utcnow)
    reviewed_at = Column(DateTime)