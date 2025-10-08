from sqlalchemy.orm import Session
from tables.logs import SystemLog

def add_log(db: Session, action: str, actor_id: int, target_table: str, target_id: int, details: dict = None):
    log = SystemLog(
        action=action,
        actor_id=actor_id,
        target_table=target_table,
        target_id=target_id,
        details=details or {}
    )
    db.add(log)
    db.commit()
    return log
