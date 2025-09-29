# app/crud.py
from sqlalchemy.orm import Session
from fastapi import HTTPException
from ... import models

def get_user_by_id(db: Session, user_id: int):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

def add_points(db: Session, user_id: int, points: int):
    user = get_user_by_id(db, user_id)
    user.points += points
    db.commit()
    db.refresh(user)
    return user

def reset_points(db: Session, user_id: int):
    user = get_user_by_id(db, user_id)
    user.points = 0
    db.commit()
    db.refresh(user)
    return user
