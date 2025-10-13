from fastapi import APIRouter, Depends, Form, UploadFile, File
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from config import get_db
from tables.tasks import Task, TaskStatus
from tables.submissions import Submission
from tables.rewards import Reward
from tables.reward_redeems import RewardRedeem
from tables.families import FamilyMember
import os, uuid, shutil

router = APIRouter(prefix="/kid", tags=["Kid Tasks/Rewards"])

UPLOAD_DIR = "static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def _save_file(upload: UploadFile) -> str:
    if not upload: return None
    name = f"{uuid.uuid4().hex}_{upload.filename}"
    path = os.path.join(UPLOAD_DIR, name)
    with open(path, "wb") as f: shutil.copyfileobj(upload.file, f)
    return path

@router.get("/tasks/{kid_id}")
def list_tasks(kid_id: int, db: Session = Depends(get_db)):
    tasks = db.query(Task).filter(
        Task.kid_id == kid_id,
        Task.status.in_([TaskStatus.assigned, TaskStatus.rejected])
    ).all()
    return {"tasks": [{"id": t.id, "title": t.title, "points": t.points, "status": t.status.value} for t in tasks]}

@router.post("/{kid_id}/task/submit/{task_id}")
def submit_task(kid_id: int, task_id: int, message: str = Form(""), file: UploadFile = File(None), db: Session = Depends(get_db)):
    task = db.get(Task, task_id)
    if not task or task.kid_id != kid_id:
        return RedirectResponse(f"/kid/tasks/{kid_id}?err=no_task", status_code=303)
    path = _save_file(file) if file else None
    db.add(Submission(task_id=task_id, kid_id=kid_id, message=message.strip(), evidence_path=path))
    task.status = TaskStatus.submitted
    db.commit()
    return RedirectResponse(f"/kid/tasks/{kid_id}?ok=submitted", status_code=303)

@router.get("/rewards/{kid_id}")
def list_rewards(kid_id: int, db: Session = Depends(get_db)):
    fam = db.query(FamilyMember).filter(FamilyMember.user_id == kid_id).first()
    if not fam: return {"rewards": []}
    rewards = db.query(Reward).all()  # MVP: เอาของในบ้านเดียวกันค่อยปรับทีหลัง
    return {"rewards": [{"id": r.id, "name": r.name, "cost": r.cost} for r in rewards]}

@router.post("/{kid_id}/redeem/{reward_id}")
def redeem_reward(kid_id: int, reward_id: int, db: Session = Depends(get_db)):
    exists = db.query(RewardRedeem).filter(
        RewardRedeem.kid_id == kid_id,
        RewardRedeem.reward_id == reward_id,
        RewardRedeem.status == "pending"
    ).first()
    if exists:
        return RedirectResponse(f"/kid/rewards/{kid_id}?err=dup", status_code=303)
    db.add(RewardRedeem(reward_id=reward_id, kid_id=kid_id)); db.commit()
    return RedirectResponse(f"/kid/rewards/{kid_id}?ok=requested", status_code=303)