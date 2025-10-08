from fastapi import APIRouter, Request, Form, Depends, UploadFile, File
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from config import get_db
from tables import users, tasks, submissions, rewards
from tables.reward_redeems import RewardRedeem
from tables.notifications import NotiType, Notification
from core.notify import push_noti, unread_count
from core.logger import add_log
import os, shutil, uuid

router = APIRouter(prefix="/kid", tags=["Kid Pages"])
templates = Jinja2Templates(directory="templates")

UPLOAD_DIR = "static/uploads/submissions"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def save_file(file: UploadFile):
    filename = f"{uuid.uuid4().hex}_{file.filename}"
    path = os.path.join(UPLOAD_DIR, filename)
    with open(path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return path

@router.get("/dashboard/{kid_id}")
def dashboard_kid(request: Request, kid_id: int, db: Session = Depends(get_db)):
    kid = db.get(users.Users, kid_id)
    task_list = db.query(tasks.Task).filter(tasks.Task.kid_id == kid_id).all()
    rewards_list = db.query(rewards.Reward).all()
    subs = db.query(submissions.Submission).filter(submissions.Submission.kid_id == kid_id).all()
    notis = db.query(Notification).filter(Notification.to_user_id == kid_id).order_by(Notification.created_at.desc()).limit(20).all()
    uc = unread_count(db, kid_id)
    return templates.TemplateResponse("dashboard_kid.html", {
        "request": request, "kid": kid, "tasks": task_list, "rewards": rewards_list, "subs": subs,
        "notis": notis, "unread": uc, "role": "kid", "kid_id": kid_id
    })

@router.post("/submit/{task_id}")
def submit_task(task_id: int, kid_id: int = Form(...), message: str = Form(""),
                file: UploadFile = File(None), db: Session = Depends(get_db)):
    path = save_file(file) if file else None
    s = submissions.Submission(task_id=task_id, kid_id=kid_id, message=message, evidence_path=path)
    db.add(s); db.commit()

    task = db.get(tasks.Task, task_id)
    push_noti(db, to_user_id=task.parent_id, actor_user_id=kid_id,
              type=NotiType.submission_submitted, entity="submission", entity_id=s.id,
              message=f"เด็กส่งงาน: {task.title}")
    add_log(db, "submission_create", kid_id, "submissions", s.id, {"message": message})
    return RedirectResponse(f"/kid/dashboard/{kid_id}", status_code=303)

@router.post("/reward/redeem/{rid}")
def redeem_reward(rid: int, kid_id: int = Form(...), db: Session = Depends(get_db)):
    rr = RewardRedeem(reward_id=rid, kid_id=kid_id)
    db.add(rr); db.commit()

    parents = db.query(users.Users).filter(users.Users.role == "parent").all()
    for p in parents:
        push_noti(db, to_user_id=p.id, actor_user_id=kid_id,
                  type=NotiType.reward_redeem_request, entity="reward_redeem", entity_id=rr.id,
                  message=f"คำขอแลกรางวัล #{rr.id}")
    add_log(db, "reward_redeem_request", kid_id, "reward_redeems", rr.id, {})
    return RedirectResponse(f"/kid/dashboard/{kid_id}", status_code=303)
