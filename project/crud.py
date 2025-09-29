from sqlalchemy.orm import Session
import models, schemas

def create_parent(db: Session, parent: schemas.ParentCreate):
    db_parent = models.Parent(**parent.dict())
    db.add(db_parent)
    db.commit()
    db.refresh(db_parent)
    return db_parent

def get_parents(db: Session):
    return db.query(models.Parent).all()

def create_student(db: Session, student: schemas.StudentCreate, parent_id: int):
    db_parent = db.query(models.Parent).filter(models.Parent.id == parent_id).first()
    if not db_parent:
        return None
    db_student = models.Student(**student.dict(), parent_id=parent_id)
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    return db_student

def get_students(db: Session):
    return db.query(models.Student).all()
