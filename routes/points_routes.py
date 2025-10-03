"""
Router สำหรับระบบแต้ม (Point System)
- ดูแต้มรวมของเด็ก
- ดูประวัติการได้รับแต้ม
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from config import get_db
from tables.points_history import PointsHistory
from tables.users import User
from models.points import PointsOut, PointsHistoryOut

router = APIRouter(prefix="/points", tags=["Points"])

@router.get("/{child_id}", response_model=PointsOut)
def get_points(child_id: int, db: Session = Depends(get_db)):
    """
    ดึงแต้มรวมของเด็กจาก user.points
    """
    child = db.get(User, child_id)
    if not child:
        raise HTTPException(404, "Child not found")
    return PointsOut(child_id=child.id, total_points=child.points)

@router.get("/{child_id}/history", response_model=List[PointsHistoryOut])
def get_history(child_id: int, db: Session = Depends(get_db)):
    """
    ดึงประวัติการได้รับแต้มทั้งหมดของเด็ก (เรียงจากใหม่ไปเก่า)
    """
    history = (
        db.query(PointsHistory)
        .filter(PointsHistory.child_id == child_id)
        .order_by(PointsHistory.created_at.desc())
        .all()
    )
    return history
