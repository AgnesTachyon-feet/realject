from sqlalchemy.orm import Session
from tables.notifications import Notification, NotiType

def push_noti(db: Session, *, to_user_id: int, actor_user_id: int,
              type: NotiType, entity: str, entity_id: int, message: str):
    n = Notification(
        to_user_id=to_user_id,
        actor_user_id=actor_user_id,
        type=type,
        entity=entity,
        entity_id=entity_id,
        message=message
    )
    db.add(n)
    db.commit()
    return n

def unread_count(db: Session, user_id: int) -> int:
    return db.query(Notification).filter(
        Notification.to_user_id == user_id,
        Notification.is_read == False
    ).count()
