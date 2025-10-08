"""
Router ของ Submission ใช้สำหรับเด็กส่งงาน และ parent ยืนยัน/ปฏิเสธงาน
(ตัด notification และ point system ออกไปก่อน เพื่อให้รันได้)
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from datetime import datetime
import os, shutil, uuid
from typing import List

from config import get_db
from tables.submission import Submission, SubmissionStatus
from tables.task import Task
from models.submission import SubmissionCreate, SubmissionDecision, SubmissionOut

router = APIRouter(prefix="/submissions", tags=["Submissions"])

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def save_file(upload: UploadFile) -> str:
    filename = f"{uuid.uuid4().hex}_{upload.filename}"
    path = os.path.join(UPLOAD_DIR, filename)
    with open(path, "wb") as buffer:
        shutil.copyfileobj(upload.file, buffer)
    return path


@router.post("/", response_model=SubmissionOut)
async def submit_task(
    task_id: int,
    child_id: int,
    message: str = None,
    file: UploadFile = File(None),
    db: Session = Depends(get_db),
):
    """
    Endpoint ให้เด็กส่งงาน โดยแนบข้อความและไฟล์ (ออปชัน)
    """
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    if task.child_id != child_id:
        raise HTTPException(400, "This task is not assigned to this child")

    evidence_path = save_file(file) if file else None
    submission = Submission(
        task_id=task_id,
        child_id=child_id,
        evidence_path=evidence_path,
        message=message
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)

    return submission


@router.patch("/{submission_id}/decision", response_model=SubmissionOut)
def decide_submission(submission_id: int, decision: SubmissionDecision, db: Session = Depends(get_db)):
    """
    Endpoint ให้ parent ตัดสินใจ (อนุมัติ/ปฏิเสธ) งานที่เด็กส่ง
    """
    submission = db.get(Submission, submission_id)
    if not submission:
        raise HTTPException(404, "Submission not found")

    task = db.get(Task, submission.task_id)
    if not task or task.parent_id != decision.parent_id:
        raise HTTPException(403, "Not authorized")

    if decision.approve:
        submission.status = SubmissionStatus.approved
        submission.reviewed_at = datetime.utcnow()
    else:
        submission.status = SubmissionStatus.rejected
        submission.reviewed_at = datetime.utcnow()

    db.commit()
    db.refresh(submission)
    return submission
