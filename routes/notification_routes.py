"""
Router สำหรับ Notification
รองรับการดึงรายการแจ้งเตือน และเปลี่ยนสถานะว่าอ่านแล้ว
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from config import get_db
from tables.notification import Notification
from models.notification import NotificationOut

router = APIRouter(prefix="/notifications", tags=["Notifications"])

@router.get("/{user_id}", response_model=List[NotificationOut])
def get_notifications(user_id: int, db: Session = Depends(get_db)):
    """
    ดึงรายการแจ้งเตือนทั้งหมดของผู้ใช้ตาม user_id
    เรียงจากใหม่ไปเก่า
    """
    notes = db.query(Notification).filter(Notification.user_id == user_id).order_by(Notification.created_at.desc()).all()
    return notes

@router.patch("/{notification_id}/read", response_model=NotificationOut)
def mark_as_read(notification_id: int, db: Session = Depends(get_db)):
    """
    อัปเดตสถานะการแจ้งเตือนเป็น 'อ่านแล้ว'
    """
    note = db.get(Notification, notification_id)
    if not note:
        raise HTTPException(404, "Notification not found")
    note.is_read = True
    db.commit()
    db.refresh(note)
    return note
