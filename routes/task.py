"""
ไฟล์นี้ประกาศ FastAPI Router สำหรับ Task
Router นี้จะมี endpoint สำหรับสร้างภารกิจใหม่ และดึงภารกิจของเด็ก
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from config import get_db
from tables.task import Task
from models.task import TaskCreate, TaskOut

router = APIRouter(prefix="/tasks", tags=["Tasks"])

@router.post("/", response_model=TaskOut)
def create_task(task_in: TaskCreate, db: Session = Depends(get_db)):
    """
    Endpoint นี้ใช้สำหรับสร้างภารกิจใหม่
    รับข้อมูลจาก parent และบันทึกลงตาราง tasks
    """
    task = Task(
        title=task_in.title,
        description=task_in.description,
        due_date=task_in.due_date,
        points=task_in.points,
        parent_id=task_in.parent_id,
        child_id=task_in.child_id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task

@router.get("/child/{child_id}", response_model=List[TaskOut])
def get_tasks_for_child(child_id: int, db: Session = Depends(get_db)):
    """
    Endpoint นี้ใช้ดึงรายการภารกิจที่มอบหมายให้เด็ก
    โดยใช้ child_id ในการค้นหา
    """
    tasks = (
        db.query(Task)
        .filter(Task.child_id == child_id)
        .order_by(Task.created_at.desc())
        .all()
    )
    return tasks