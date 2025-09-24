# family.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import models, schemas, crud
from database import get_db

# สร้าง router แทนที่จะเป็น FastAPI instance ตรง ๆ
router = APIRouter(
    prefix="/family",
    tags=["family"]
)

@router.post("/parents/", response_model=schemas.ParentResponse)
def create_parent(parent: schemas.ParentCreate, db: Session = Depends(get_db)):
    return crud.create_parent(db=db, parent=parent)

@router.get("/parents/", response_model=list[schemas.ParentResponse])
def read_parents(db: Session = Depends(get_db)):
    return crud.get_parents(db=db)

@router.post("/students/", response_model=schemas.StudentResponse)
def create_student(student: schemas.StudentCreate, parent_id: int, db: Session = Depends(get_db)):
    db_student = crud.create_student(db=db, student=student, parent_id=parent_id)
    if not db_student:
        raise HTTPException(status_code=404, detail="Parent not found")
    return db_student

@router.get("/students/", response_model=list[schemas.StudentResponse])
def read_students(db: Session = Depends(get_db)):
    return crud.get_students(db=db)
