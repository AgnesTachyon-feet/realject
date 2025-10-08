from sqlalchemy import Column, Integer, String, DateTime, Boolean, Enum
from datetime import datetime
import enum
from config import Base

class NotiType(str, enum.Enum):
    submission_submitted = "submission_submitted"
    submission_approved  = "submission_approved"
    submission_rejected  = "submission_rejected"
    reward_redeem_request = "reward_redeem_request"
    reward_redeem_approved = "reward_redeem_approved"
    reward_redeem_rejected = "reward_redeem_rejected"

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True)
    to_user_id = Column(Integer, index=True, nullable=False)
    actor_user_id = Column(Integer, nullable=False)
    type = Column(Enum(NotiType), nullable=False)
    entity = Column(String, nullable=False)      # "submission" | "reward_redeem"
    entity_id = Column(Integer, nullable=False)
    message = Column(String, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
