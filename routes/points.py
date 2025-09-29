# app/routers/points.py
from fastapi import APIRouter, Depends, HTTPException
from . import crud
from sqlalchemy.orm import Session
from ... import schemas, database

router = APIRouter(
    prefix="/points",
    tags=["Points System"]
)

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/{user_id}/add", response_model=schemas.UserResponse)
def add_points(user_id: int, points: int, db: Session = Depends(get_db)):
    if points <= 0:
        raise HTTPException(status_code=400, detail="Points must be greater than 0")
    return crud.add_points(db, user_id, points)

@router.post("/{user_id}/reset", response_model=schemas.UserResponse)
def reset_points(user_id: int, db: Session = Depends(get_db)):
    return crud.reset_points(db, user_id)
